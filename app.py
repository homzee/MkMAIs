import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="AI電商内容生成助手", layout="wide")

st.title("🛍️ AI電商内容生成助手")
st.markdown("從商品名稱與關鍵字，自動生成多語言圖文與短視頻腳本")

# 用户输入表单
with st.form("input_form"):
    product_name = st.text_input("商品名稱*", "")
    keywords = st.text_input("關鍵字（以逗號分隔）", "")
    selling_points = st.text_area("商品賣點", "")
    languages = st.multiselect("輸出語言*", ["中文", "日文", "英文"], default=["中文"])
    style = st.selectbox("風格", ["簡潔", "專業", "SNS風", "SEO強化"])
    generate_video = st.checkbox("附帶短視頻腳本", value=True)
    submitted = st.form_submit_button("生成內容")

if submitted and product_name and languages:
    with st.spinner("正在連接 OpenAI 生成內容..."):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        lang_str = "、".join(languages)
        video_flag = "需要短視頻腳本" if generate_video else "不需要短視頻腳本"

        prompt = f"""你是一位專精於電商商品文案撰寫的多語內容生成AI，請根據以下商品信息生成內容：

【商品名】：{product_name}
【關鍵字】：{keywords}
【賣點】：{selling_points}
【語言】：{lang_str}
【風格】：{style}
【附加】：{video_flag}

請輸出以下格式內容：
1. 標題（30字內）
2. 子標題（40~60字）
3. 主文案正文（分3段）
4. SNS推薦短句
5. 商品賣點摘要（3條）
6. 短視頻字幕腳本（分5~10句字幕）
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位專業的多語電商文案撰寫AI"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        output = response.choices[0].message.content
        st.success("✅ 已成功生成內容")
        st.text_area("🔽 生成結果", output, height=500)
