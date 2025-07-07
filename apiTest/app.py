import pyupbit
import os
import pandas as pd
import time
import datetime

# 🚨 API 키를 입력하세요.
UPBIT_ACCESS_KEY = os.environ.get('UPBIT_ACCESS_KEY')
UPBIT_SECRET_KEY = os.environ.get('UPBIT_SECRET_KEY')  # 본인의 Secret Key

# --- 전략 설정 ---
MAX_POSITIONS = 3  # 최대 보유 코인 수
INVESTMENT_KRW = 10000  # 코인 당 1회 매수 금액 (업비트 최소 주문금액 이상)
STOP_LOSS_PCT = 0.05  # 손절 비율 (5%)

# BNF 전략 파라미터
MA_PERIOD = 25  # 이동평균선 기간 (일)
RSI_PERIOD = 14  # RSI 계산 기간 (일)
RSI_OVERSOLD = 30  # RSI 과매도 기준
DISPARITY_THRESHOLD = 85  # 이격도 과매도 기준 (%)


def get_current_balance(ticker):
    """지정된 티커 또는 KRW의 잔고를 조회합니다."""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            return float(b['balance'])
    return 0


def calculate_indicators(df):
    """데이터프레임을 받아 기술적 지표를 계산하고 추가합니다."""
    # 25일 이동평균
    df['ma25'] = df['close'].rolling(window=MA_PERIOD).mean()
    # 이격도 (Disparity)
    df['disparity'] = (df['close'] / df['ma25']) * 100
    # 14일 RSI
    delta = df['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
    rs = gain / loss
    df['rsi14'] = 100 - (100 / (1 + rs))
    return df


# --- 메인 로직 ---
print("BNF 멀티코인 스캐너 자동매매를 시작합니다. (API 요청 제한 준수 버전)")
print(f"최대 보유 코인 수: {MAX_POSITIONS}개")

try:
    upbit = pyupbit.Upbit(UPBIT_ACCESS_KEY, UPBIT_SECRET_KEY)
    krw_balance = get_current_balance("KRW")
    print(f"현재 KRW 잔고: {krw_balance:,.0f} 원")
except Exception as e:
    print(f"API 연결 오류: {e}")
    exit()

# 현재 보유 포지션 관리 (ticker: purchase_price)
positions = {}

while True:
    try:
        # 1. 업비트 KRW 마켓의 모든 티커 목록 가져오기
        all_tickers = pyupbit.get_tickers(fiat="KRW")
        print(
            f"\n--- {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 현재 보유: {len(positions)}개 | 스캔 대상: {len(all_tickers)}개 ---")

        for ticker in all_tickers:
            # 🚨 중요: API 요청 수 제한(초당 10회)을 준수하기 위한 딜레이
            # 각 코인마다 최소 2번의 API 요청(get_ohlcv, get_current_price)이 발생하므로,
            # 0.22초의 딜레이를 주어 초당 약 4.5개 코인(API 요청 9회)을 처리하도록 조절합니다.
            time.sleep(0.22)

            # 2. 이미 보유한 코인인 경우 (매도 조건 확인)
            if ticker in positions:
                df_day = pyupbit.get_ohlcv(ticker, interval="day", count=MA_PERIOD)
                current_price = pyupbit.get_current_price(ticker)

                if df_day is None or current_price is None:
                    continue

                ma25 = df_day['close'].rolling(window=MA_PERIOD).mean().iloc[-1]
                purchase_price = positions[ticker]
                stop_loss_price = purchase_price * (1 - STOP_LOSS_PCT)

                # 익절 조건: 현재가가 25일 이평선 이상으로 반등
                if current_price >= ma25:
                    print(f"✅ [익절] {ticker}: 목표가 도달. 전량 매도")
                    coin_balance = get_current_balance(ticker.split('-')[1])
                    if coin_balance > 0:
                        upbit.sell_market_order(ticker, coin_balance)
                    del positions[ticker]
                # 손절 조건: 매수 가격보다 설정된 비율 이상 하락
                elif current_price <= stop_loss_price:
                    print(f"🔻 [손절] {ticker}: 손절가 도달. 전량 매도")
                    coin_balance = get_current_balance(ticker.split('-')[1])
                    if coin_balance > 0:
                        upbit.sell_market_order(ticker, coin_balance)
                    del positions[ticker]
                else:
                    print(
                        f"   (보유중) {ticker} | 현재가: {current_price:,.0f} | 매수가: {purchase_price:,.0f} | 목표가(MA25): {ma25:,.0f}")

                continue  # 다음 티커로

            # 3. 신규 매수 조건 확인 (최대 보유 코인 수 미만일 때만)
            if len(positions) < MAX_POSITIONS:
                df_day = pyupbit.get_ohlcv(ticker, interval="day", count=100)
                if df_day is None or len(df_day) < MA_PERIOD:
                    continue

                df_with_indicators = calculate_indicators(df_day)
                latest_data = df_with_indicators.iloc[-1]

                # 매수 조건: 이격도와 RSI가 모두 과매도 상태
                if latest_data['disparity'] < DISPARITY_THRESHOLD and latest_data['rsi14'] < RSI_OVERSOLD:
                    print(
                        f"🎯 [매수 신호 발견] {ticker} | 이격도: {latest_data['disparity']:.2f}%, RSI: {latest_data['rsi14']:.2f}")
                    krw_balance = get_current_balance("KRW")
                    if krw_balance >= INVESTMENT_KRW:
                        print(f"   - 💰 {ticker} {INVESTMENT_KRW:,.0f}원 매수 주문 실행")
                        buy_result = upbit.buy_market_order(ticker, INVESTMENT_KRW)

                        # 매수 성공 시 포지션에 추가
                        if buy_result and 'uuid' in buy_result:
                            # 정확한 매수 평균가를 얻기 위해 잠시 대기 후 체결 내역 조회 (선택적)
                            time.sleep(2)
                            order_info = upbit.get_order(buy_result['uuid'])
                            if order_info and order_info['state'] == 'done':
                                avg_price = float(order_info['trades'][0]['price'])
                                positions[ticker] = avg_price
                                print(f"   - ✅ 매수 완료! {ticker}, 평균 매수가: {avg_price:,.0f}")
                            else:  # 체결이 바로 안되면 현재가로 기록
                                current_price = pyupbit.get_current_price(ticker)
                                positions[ticker] = current_price
                                print(f"   - ✅ 매수 주문 완료! {ticker}, 현재가: {current_price:,.0f} 기준으로 기록")

                        else:
                            print(f"   - ❌ 매수 주문 실패: {buy_result}")
                    else:
                        print("잔고 부족으로 더 이상 매수할 수 없습니다.")
                        # 잔고가 없으면 남은 코인들을 더 스캔할 필요가 없으므로 루프를 잠시 멈춤
                        time.sleep(60 * 5)  # 5분간 대기 후 다시 시도
                        break

    except Exception as e:
        print(f"🔥 메인 루프 오류 발생: {e}")
        time.sleep(60)