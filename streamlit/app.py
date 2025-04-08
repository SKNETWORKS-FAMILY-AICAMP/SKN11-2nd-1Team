import streamlit as st
import pandas as pd
import numpy as np
import pickle

# 페이지 설정
st.set_page_config(
    page_title="구독 취소 예측 시스템",
    page_icon="📉",
    layout="wide"
)

# 모델 로드
with open("rf_model.pkl", "rb") as file:
    rf_model, scaler = pickle.load(file)

# 컬럼 순서
correct_order = [
    "HH Income", "Home Ownership", "dummy for Children", "Year Of Residence",
    "Age", "weekly fee", "Deliveryperiod", "Nielsen Prizm", "reward program",
    "Working", "Gender", "Is_Online"
]

# 탭 UI
tab1, tab2 = st.tabs(["🏠 개별 예측", "📈 데이터 분석"])

# ========================
# 탭1: 개별 예측
# ========================
with tab1:
    st.markdown("""
        <style>
        section.main > div:not(:has([data-testid=\"stTabs\"])) {
            background-color: #fefefe;
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🔍 개별 사용자 이탈 예측")
    st.markdown("개별 사용자 데이터를 입력하고 버튼을 눌러 예측 결과를 확인하세요.")

    with st.form(key="prediction_form"):
        col1, col2 = st.columns(2)

        with col1:
            income = st.number_input("💰 HH Income", 10000, 100000, step=1000)
            age = st.slider("🎂 Age", 18, 90, 30)
            weekly_fee = st.number_input("💸 Weekly Fee", 0.0, 10.0, step=0.1)
            reward_program_display = st.selectbox("🎁 Reward Program", ["미참여", "참여"])
            reward_program = 0 if reward_program_display == "미참여" else 1
            delivery_period = st.slider("🚚 Delivery Period", 1, 7, 3)
            year_of_residence = st.slider("📅 Year Of Residence", 1, 30, 10)

        with col2:
            home_ownership_display = st.selectbox("🏠 Home Ownership", ["RENT", "Own"])
            home_ownership = 0 if home_ownership_display == "RENT" else 1

            children_display = st.selectbox("👶 Has Children", ["자녀 없음", "자녀 있음"])
            children = 0 if children_display == "자녀 없음" else 1

            gender_display = st.selectbox("🧑 Gender", ["남자", "여자"])
            gender = 0 if gender_display == "남자" else 1

            is_online_display = st.selectbox("🌐 Is Online", ["오프라인", "온라인"])
            is_online = 0 if is_online_display == "오프라인" else 1

            nielsen_options = [
    "MW: Male Working-age (근로 연령대 남성)",
    "MM: Male Middle-aged (중년 남성)",
    "YM: Young Man (젊은 남성)",
    "ME: Male Elderly (노년 남성)",
    "YE: Young Elderly (젊은 노년층)"
] if gender == 0 else [
    "FM: Female Middle-aged (중년 여성)",
    "FW: Female Working-age (근로 연령대 여성)",
    "YW: Young Woman (젊은 여성)",
    "FE: Female Elderly (노년 여성)",
    "YE: Young Elderly (젊은 노년층)"
]
            nielsen_prizm_display = st.selectbox("🧭 Nielsen Prizm", nielsen_options)
            nielsen_prizm = nielsen_options.index(nielsen_prizm_display)

            working_display = st.selectbox("💼 Working", ["0 : 근로 중 아님", "1 : 근로 중"])
            working = 0 if "0" in working_display else 1

        submitted = st.form_submit_button("예측 실행")

    if submitted:
        input_df = pd.DataFrame([{ 
            "HH Income": income, "Home Ownership": home_ownership,
            "dummy for Children": children, "Year Of Residence": year_of_residence,
            "Age": age, "weekly fee": weekly_fee, "Deliveryperiod": delivery_period,
            "Nielsen Prizm": nielsen_prizm, "reward program": reward_program,
            "Working": working, "Gender": gender, "Is_Online": is_online
        }])

        input_df = input_df[correct_order]
        scaled_input = scaler.transform(input_df)
        prediction = rf_model.predict(scaled_input)
        prediction_proba = rf_model.predict_proba(scaled_input)

        st.markdown("### 📢 예측 결과")
        if prediction[0] == 1:
            st.error("🚨 구독 취소 위험이 **높습니다**.")
        else:
            st.success("✅ 구독 유지 가능성이 **높습니다**.")

        st.markdown(f"**취소 위험 확률:** `{prediction_proba[0][1]:.2%}`")

        contributions = np.abs(rf_model.feature_importances_ * scaled_input[0])
        contrib_df = pd.DataFrame({"Feature": correct_order, "Contribution": contributions})
        contrib_df = contrib_df.sort_values(by="Contribution", ascending=False)

        st.markdown("**이탈에 큰 영향을 준 상위 요인:**")
        for i, row in contrib_df.head(4).iterrows():
            st.write(f"• {row['Feature']}")

# ========================
# 탭2: 데이터 분석
# ========================
with tab2:
    st.markdown("""
        <style>
        section.main > div:not(:has([data-testid=\"stTabs\"])) {
            background-color: #e8f0ff;
            padding: 2rem;
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📊 고객군 이탈 위험 분석")

    df = pd.read_excel("processed_data.xlsx")
    df_active = df[df['Subscriber'] == 0]
        
    X_active = df_active[correct_order]
    scaled_active = scaler.transform(X_active)
    df_active['Risk'] = rf_model.predict_proba(scaled_active)[:, 1]
    high_risk = df_active.sort_values(by='Risk', ascending=False).head(50)
    high_risk['Rank'] = range(1, len(high_risk) + 1)

    st.markdown("### 🔝 이탈 위험 고객 Top 50")
    st.dataframe(high_risk[['Rank'] + correct_order + ['Risk']])

    st.markdown("### 🔍 개별 분석")
    selected_index = st.selectbox("분석할 고객 순위", high_risk['Rank'])
    customer = high_risk[high_risk['Rank'] == selected_index].iloc[0]
    personal_contrib = np.abs(rf_model.feature_importances_ * scaled_active[selected_index - 1])
    personal_df = pd.DataFrame({"Feature": correct_order, "Contribution": personal_contrib})
    personal_df = personal_df.sort_values(by="Contribution", ascending=False)

    st.info(f"선택 고객의 **구독 취소 위험 확률**: `{customer['Risk']:.2%}`")
    st.markdown("**영향을 많이 준 요인:**")
    for i, row in personal_df.head(4).iterrows():
        st.write(f"• {row['Feature']}")