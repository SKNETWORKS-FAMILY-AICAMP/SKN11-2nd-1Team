import streamlit as st
import pandas as pd
import numpy as np
import pickle

# 모델 로드
with open("rf_model.pkl", "rb") as file:
    rf_model, scaler = pickle.load(file)

# 올바른 컬럼 순서
correct_order = [
    "HH Income", "Home Ownership", "dummy for Children", "Year Of Residence",
    "Age", "weekly fee", "Deliveryperiod", "Nielsen Prizm", "reward program",
    "Working", "Gender", "Is_Online"
]

# 🌟 페이지 상태를 관리하는 함수
def set_page(page_name):
    st.session_state["page"] = page_name

# 🌟 Streamlit Session State 초기화
if "page" not in st.session_state:
    st.session_state["page"] = "개별 예측"

# 네비게이션바 개선: 두 개의 버튼으로 간단히 구성
st.sidebar.title("구독 취소 위험 예측")
if st.sidebar.button("개별 예측"):
    set_page("개별 예측")
if st.sidebar.button("데이터 분석"):
    set_page("데이터 분석")

# 📝 개별 예측 페이지
if st.session_state["page"] == "개별 예측":
    st.title("개별 사용자 구독 취소 위험 예측")

    # 사용자 데이터 입력 폼
    def user_input_features():
        income = st.number_input("HH Income", min_value=10000, max_value=100000, step=1000)
        age = st.slider("Age", 18, 90, 30)
        weekly_fee = st.number_input("Weekly Fee", min_value=0.0, max_value=10.0, step=0.1)
        reward_program = st.selectbox("Reward Program", [0, 1])
        delivery_period = st.slider("Delivery Period", 1, 7, 3)
        home_ownership = st.selectbox("Home Ownership", [0, 1])
        children = st.selectbox("Has Children", [0, 1])
        gender = st.selectbox("Gender (Male: 0, Female: 1)", [0, 1])
        is_online = st.selectbox("Is Online", [0, 1])
        nielsen_prizm = st.selectbox("Nielsen Prizm (0-8)", list(range(9)))
        working = st.selectbox("Working (0: No, 1: Yes)", [0, 1])
        year_of_residence = st.slider("Year Of Residence", 1, 30, 10)

        data = {
            "HH Income": income,
            "Home Ownership": home_ownership,
            "dummy for Children": children,
            "Year Of Residence": year_of_residence,
            "Age": age,
            "weekly fee": weekly_fee,
            "Deliveryperiod": delivery_period,
            "Nielsen Prizm": nielsen_prizm,
            "reward program": reward_program,
            "Working": working,
            "Gender": gender,
            "Is_Online": is_online
        }
        return pd.DataFrame(data, index=[0])

    # 사용자 입력 받기
    input_df = user_input_features()

    # 컬럼 순서 정렬
    input_df = input_df[correct_order]

    # 예측 수행
    scaled_input = scaler.transform(input_df)
    prediction = rf_model.predict(scaled_input)
    prediction_proba = rf_model.predict_proba(scaled_input)

    st.subheader("예측 결과")
    if prediction[0] == 1:
        st.write("🚨 구독 취소 위험이 높습니다.")
    else:
        st.write("✅ 구독 유지 가능성이 높습니다.")

    st.write(f"**취소 위험 확률:** {prediction_proba[0][1]:.2%}")

    # 기여도 계산 (절대값 사용하여 기여도 명확히 표현)
    feature_contributions = np.abs(rf_model.feature_importances_ * scaled_input[0])
    contribution_df = pd.DataFrame({"Feature": correct_order, "Contribution": feature_contributions})
    contribution_df = contribution_df.sort_values(by="Contribution", ascending=False)

    # 영향력이 큰 변수 상위 4개 표시 (값 없이 이름만)
    top_contributions = contribution_df.head(4)
    st.write("**이탈 가능성에 크게 기여하는 요소:**")
    for idx, row in top_contributions.iterrows():
        st.write(f"- {row['Feature']}")

# 📊 데이터 분석 페이지
elif st.session_state["page"] == "데이터 분석":
    st.title("구독 중 고객 중 이탈 위험 분석")

    # 데이터 불러오기
    file_path = "processed_data.xlsx"
    df = pd.read_excel(file_path)

    # Subscriber가 0인 데이터만 필터링
    df_active = df[df['Subscriber'] == 0]

    # 데이터 전처리 (스케일링)
    X_active = df_active[correct_order]
    scaled_active = scaler.transform(X_active)

    # 구독 위험 예측
    df_active['Risk'] = rf_model.predict_proba(scaled_active)[:, 1]

    # 취소 위험이 높은 순으로 정렬
    high_risk = df_active.sort_values(by='Risk', ascending=False).head(50)

    # 시각화용 데이터 준비
    high_risk['Rank'] = range(1, len(high_risk) + 1)

    # 상위 50명 표시 (모든 사용한 컬럼 포함)
    st.subheader("구독 취소 위험이 높은 고객 Top 50")
    st.dataframe(high_risk[['Rank'] + correct_order + ['Risk']])

    # 상세 분석 버튼
    st.subheader("개별 구독자 위험 요인 분석")
    selected_index = st.selectbox("분석할 고객 순위 선택", high_risk['Rank'])
    selected_customer = high_risk[high_risk['Rank'] == selected_index].iloc[0]

    # 개인별 위험 요인 분석
    personal_contributions = np.abs(rf_model.feature_importances_ * scaled_active[selected_index - 1])
    personal_contribution_df = pd.DataFrame({"Feature": correct_order, "Contribution": personal_contributions})
    personal_contribution_df = personal_contribution_df.sort_values(by="Contribution", ascending=False)

    st.write(f"**선택된 고객의 취소 위험 확률:** {selected_customer['Risk']:.2%}")
    st.write("**취소 가능성에 크게 기여하는 요소:**")
    for idx, row in personal_contribution_df.head(4).iterrows():
        st.write(f"- {row['Feature']}")
