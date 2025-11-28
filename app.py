import streamlit as st
import pandas as pd
import io # 用于处理内存中的文件流

# 1. 设置网页标题
st.title('🔍 智能关键词批量匹配助手')

st.markdown("""
### 📢 使用说明
1. **数据源**：包含关键词和匹配数据的 Excel。
2. **待分析文件**：包含大量文本的 Excel，程序将逐行分析这些文本。
""")

# --- 全局变量用于存储数据源DataFrame ---
df_source = None
keyword_col = None

# 2. 上传数据源文件 (包含关键词和匹配数据)
st.header('第一步：上传数据源 (包含【关键词】和【数据】)')
uploaded_source_file = st.file_uploader("请上传【数据源】Excel 文件", type=['xlsx'], key="source")

if uploaded_source_file is not None:
    # 读取 Excel 文件
    try:
        df_source = pd.read_excel(uploaded_source_file)
        st.success('✅ 数据源加载成功！')
        # 让用户选择哪一列是“关键词”列
        keyword_col = st.selectbox("请选择数据源中作为【关键词】的列名：", df_source.columns)
        st.write(f"已选择 **{keyword_col}** 列作为匹配关键词。")
        st.write("数据源前5行预览：", df_source.head())
        
    except Exception as e:
        st.error(f"数据源文件读取失败: {e}")
        df_source = None

# 3. 上传待分析文本文件 (包含要分析的文本)
st.header('第二步：上传待分析文件 (包含【文本】)')
uploaded_text_file = st.file_uploader("请上传【待分析文本】Excel 文件", type=['xlsx'], key="text")

if uploaded_text_file is not None:
    # 读取待分析文件
    try:
        df_text = pd.read_excel(uploaded_text_file)
        st.success('✅ 待分析文件加载成功！')
        # 让用户选择哪一列是“待分析文本”列
        text_col = st.selectbox("请选择待分析文件中包含【文本】的列名：", df_text.columns)
        st.write(f"已选择 **{text_col}** 列作为待分析文本。")
        st.write("待分析文件前5行预览：", df_text.head())
        
    except Exception as e:
        st.error(f"待分析文件读取失败: {e}")
        df_text = None
        
    # 4. 点击按钮开始匹配
    if df_source is not None and df_text is not None and st.button('🚀 开始批量提取与匹配'):
        st.markdown("---")
        st.subheader("处理中...")
        
        # 结果将存储在这里
        final_results = []
        
        # --- 核心批量匹配逻辑开始 (修正版：保留所有行) ---
        
        # 1. 创建关键词到数据源行的快速映射字典
        source_map = df_source.set_index(keyword_col).to_dict('index')
        all_keywords = df_source[keyword_col].tolist()
        
        # 2. 构造单个、强大的正则表达式模式
        import re
        escaped_keywords = [re.escape(str(k)) for k in all_keywords if str(k).strip()]
        
        if not escaped_keywords:
            st.warning("数据源中没有有效的关键词，请检查！")
            st.stop()

        pattern = r"({})".format('|'.join(escaped_keywords))
        
        # 结果将存储在这里
        final_results = []
        
        # 预先确定要添加的匹配列名 (用于确保所有行都有这些列)
        match_cols = ['匹配关键词'] + [f'匹配_{c}' for c in df_source.columns if c != keyword_col]
        
        with st.spinner('正在逐行分析并保留所有数据...'):
            
            # 3. 遍历待分析文件的每一行文本
            for index, text_row in df_text.iterrows():
                text_to_analyze = str(text_row[text_col])
                
                # 初始化当前行数据：包含原始数据
                current_row_data = text_row.to_dict()
                
                # 初始化匹配列为空值
                for col_name in match_cols:
                    current_row_data[col_name] = None # 或 pd.NA, None更通用
                
                # 4. 使用正则模式查找匹配项
                matches = re.findall(pattern, text_to_analyze)
                
                # 5. 【关键修正】: 无论是否匹配，都处理并添加到结果集
                if matches:
                    matched_keyword = matches[0] 
                    source_data = source_map.get(matched_keyword)
                    
                    if source_data:
                        # 发现匹配项，填充匹配列
                        current_row_data['匹配关键词'] = matched_keyword
                        
                        # 添加数据源的匹配信息
                        for col_name, value in source_data.items():
                             # 注意这里只针对数据源的列进行赋值，不覆盖原始列
                             current_row_data[f'匹配_{col_name}'] = value
                
                # 无论是否匹配到，都将当前行数据（包含原始数据和填充后的匹配信息）添加到最终结果中
                final_results.append(current_row_data)

        # --- 核心批量匹配逻辑结束 (修正版：保留所有行) ---

        # 5. 显示和下载结果
        if final_results:
            result_df = pd.DataFrame(final_results)
            st.success("✅ 批量匹配完成！")
            st.markdown("### 匹配结果预览：")
            st.dataframe(result_df) # 使用 dataframe 显示完整表格

            # 转换DataFrame为CSV格式，并确保中文不乱码
            csv_data = result_df.to_csv(index=False).encode('utf-8')

            # 添加下载按钮
            st.download_button(
                label="📥 点击下载完整结果 (CSV)",
                data=csv_data,
                file_name='批量匹配结果.csv',
                mime='text/csv',
            )
            st.balloons()
        else:
            st.info("批量分析完成，但没有在待分析文件中找到任何关键词。")