import streamlit as st
from openai import OpenAI
from openai._exceptions import APIError, RateLimitError
import datetime

st.set_page_config(page_title="AI電商内容生成助手", layout="wide")
st.title("🛍️ AI電商内容生成助手")
st.markdown("從商品名稱與關鍵字，自動生成多語言圖文、短視頻腳本與客服問答")

# 商品賣點詞庫
predefined_points = [
    "可折疊", "防水材質", "多功能", "可拆洗", "節省空間", "免安裝",
    "兒童適用", "日系設計", "便於收納", "環保材質"
]

with st.form("input_form"):
    product_name = st.text_input("商品名稱*", "")
    keywords = st.text_input("關鍵字（以逗號分隔）", "")
    selected_points = st.multiselect("選擇商品賣點（可多選）", predefined_points)
    custom_point = st.text_input("或補充其他賣點")
    languages = st.multiselect("輸出語言*", ["中文", "日文", "英文"], default=["中文", "日文"])
    style = st.selectbox("風格", ["簡潔", "專業", "SNS風", "SEO強化"])
    generate_video = st.checkbox("附帶短視頻腳本", value=True)
    generate_faq = st.checkbox("生成客服問答腳本", value=True)
    submitted = st.form_submit_button("生成內容")

selling_points = ", ".join(selected_points + ([custom_point] if custom_point else []))

if submitted and product_name and languages:
    with st.spinner("正在連接 OpenAI 生成內容..."):
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        video_flag = "需要短視頻腳本" if generate_video else "不需要短視頻腳本"

        prompt_base = f"""你是一位專精於電商商品文案撰寫的多語內容生成AI，請根據以下商品信息生成內容：

【商品名】：{product_name}
【關鍵字】：{keywords}
【賣點】：{selling_points}
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

        if generate_faq:
            faq_prompt = f"""根據以下商品信息，請生成常見客服問答腳本（Q&A格式，5組）：
【商品名】：{product_name}
【關鍵字】：{keywords}
【賣點】：{selling_points}
請使用中文。"""

        model_list = ["gpt-4o", "gpt-3.5-turbo"]
        lang_outputs = {}
        faq_output = ""

        for lang in languages:
            prompt = f"{prompt_base}\n請以 {lang} 輸出所有內容。"

            for model in model_list:
                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "你是一位專業的多語電商文案撰寫AI"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                    )
                    lang_outputs[lang] = {
                        "model": model,
                        "content": response.choices[0].message.content
                    }
                    break
                except RateLimitError:
                    st.warning(f"⚠️ {lang}：模型 {model} 被限流，嘗試降級...")
                except APIError as e:
                    st.error(f"❌ {lang}：OpenAI API 錯誤：{str(e)}")
                    break

        if generate_faq:
            try:
                faq_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "你是一位擅長客服對話模擬的電商AI"},
                        {"role": "user", "content": faq_prompt}
                    ],
                    temperature=0.6,
                )
                faq_output = faq_response.choices[0].message.content
            except Exception as e:
                st.error(f"FAQ 生成失敗：{str(e)}")

    if lang_outputs:
        cols = st.columns(len(lang_outputs))
        for i, (lang, result) in enumerate(lang_outputs.items()):
            with cols[i]:
                st.markdown(f"#### {lang}（使用模型：{result['model']}）")
                st.text_area(f"生成內容 - {lang}", result["content"], height=400)

        if faq_output:
            st.markdown("### 💬 客服問答腳本")
            st.text_area("FAQ 輸出（中文）", faq_output, height=300)

        # Markdown 匯出
        full_md = f"# 商品內容自動生成\n\n**商品名稱**：{product_name}\n**關鍵字**：{keywords}\n**賣點**：{selling_points}\n**風格**：{style}\n\n"

        for lang, res in lang_outputs.items():
            full_md += f"\n## 語言：{lang}（模型：{res['model']}）\n```\n{res['content']}\n```\n"

        if faq_output:
            full_md += f"\n## 客服問答（中文）\n```\n{faq_output}\n```\n"

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("📥 下載 Markdown", full_md, file_name=f"{product_name}_生成內容_{timestamp}.md")

    else:
        st.error("⚠️ 所有語言均未成功生成，請稍後再試或檢查 API。")
