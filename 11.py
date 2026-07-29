import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 网页全局中文字体（页面文字正常）
st.markdown("""
<style>
@import url('https://cdn.bootcdn.net/ajax/libs/noto-sans-sc/10.000/css/all.css');
* {
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.st-title, .st-header, .st-subheader, .st-markdown, .st-text, .stMetric {
    font-family: 'Noto Sans SC', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# 页面配置（仅一次）
st.set_page_config(
    page_title="2023年1-12月用电数据展示平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局卡片样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2E86AB;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.8rem;
    font-weight: bold;
    color: #A23B72;
    margin-top: 2rem;
    margin-bottom: 1rem;
    border-left: 5px solid #F18F01;
    padding-left: 1rem;
}
.card {
    background-color: #F8F9FA;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0.1);
}
.stat-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: #C73E1D;
}
.stat-label {
    font-size: 1rem;
    color: #666;
}
.area-name {
    font-weight: bold;
    color: #2E86AB;
}
</style>
""", unsafe_allow_html=True)

# 数据加载和预处理函数
@st.cache_data
def load_and_preprocess_data():
    # 读取1-12月数据文件
    df = pd.read_csv('data_2023_12.csv')
    
    # 处理时间
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['日期'] = df['timestamp'].dt.date
    df['月份'] = df['timestamp'].dt.month
    
    # 筛选有效用电数据
    valid_data = df[df['全社会用电总计'].notna()].copy()
    
    # 区域列名映射
    area_mapping = {
        "宝安供电局_0h": "A地",
        "大鹏供电局_0h": "B地",
        "福田供电局_0h": "C地",
        "光明供电局_0h": "D地",
        "龙岗供电局_0h": "E地",
        "龙华供电局_0h": "F地",
        "罗湖供电局_0h": "G地",
        "南山供电局_0h": "H地",
        "坪山供电局_0h": "I地",
        "深汕特别合作区供电局_0h": "J地",
        "盐田供电局_0h": "K地"
    }
    # 一次性批量重命名，不要循环多次rename，效率更高且不出错
    valid_data.rename(columns=area_mapping, inplace=True)
    clean_area_cols = list(area_mapping.values())
    
    # 按月聚合各区域用电量透视表（亿kWh）
    monthly_area_pivot = valid_data.groupby('月份')[clean_area_cols].mean()
    monthly_area_pivot = monthly_area_pivot / 1e8
    
    # 产业用电映射
    industry_mapping = {
        '　　第一产业': '第一产业',
        '　　第二产业': '第二产业', 
        '　　第三产业': '第三产业',
        '　B、城乡居民生活用电合计': '居民生活用电'
    }
    industry_data = valid_data[list(industry_mapping.keys())].copy()
    industry_data.columns = list(industry_mapping.values())
    industry_avg = industry_data.mean()
    total_industry = industry_avg.sum()
    industry_ratio = (industry_avg / total_industry * 100).round(2)
    
    # 总体统计
    total_stats = {
        'max_total': valid_data['全社会用电总计'].max(),
        'min_total': valid_data['全社会用电总计'].min(),
        'avg_total': valid_data['全社会用电总计'].mean(),
        'median_total': valid_data['全社会用电总计'].median(),
        'std_total': valid_data['全社会用电总计'].std(),
        'record_count': len(valid_data)
    }
    
    # 区域整体统计
    area_stats = pd.DataFrame({
        '平均用电量': valid_data[clean_area_cols].mean(),
        '最大用电量': valid_data[clean_area_cols].max(),
        '最小用电量': valid_data[clean_area_cols].min(),
        '用电量占比(%)': (valid_data[clean_area_cols].mean() / valid_data[clean_area_cols].sum() * 100).round(2)
    }).sort_values('平均用电量', ascending=False)
    
    # 全行业月度趋势
    monthly_trend = valid_data.groupby('月份').agg({
        '全社会用电总计': 'mean',
        '　　第二产业': 'mean',
        '　　第三产业': 'mean',
        '　B、城乡居民生活用电合计': 'mean'
    }).round(2)
    monthly_trend.columns = ['总用电量', '第二产业', '第三产业', '居民生活用电']
    
    return {
        'raw_data': valid_data,
        'total_stats': total_stats,
        'industry_data': industry_data,
        'industry_avg': industry_avg,
        'industry_ratio': industry_ratio,
        'area_stats': area_stats,
        'monthly_trend': monthly_trend,
        'area_columns': clean_area_cols,
        'time_range': (valid_data['timestamp'].min(), valid_data['timestamp'].max()),
        'monthly_area_pivot': monthly_area_pivot
    }

# 加载数据
data = load_and_preprocess_data()

# 侧边栏导航
st.sidebar.title("📊 用电数据导航")
section = st.sidebar.radio(
    "选择查看内容",
    ["首页数据概览", "区域用电分析"],
    index=0
)

# ===================== 一、首页数据概览 =====================
if section == "首页数据概览":
    st.markdown('<h1 class="main-header">2023年1-12月用电数据展示平台</h1>', unsafe_allow_html=True)
    
    st.markdown('<h2 class="section-header">一、数据基本信息</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        start_date = data['time_range'][0].strftime('%Y年%m月%d日')
        end_date = data['time_range'][1].strftime('%Y年%m月%d日')
        st.markdown(f'<div class="stat-label">数据时间跨度</div><div class="stat-value">{start_date} - {end_date}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">有效数据记录数</div><div class="stat-value">{data["total_stats"]["record_count"]:,} 条</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-label">覆盖行政区域数</div><div class="stat-value">{len(data["area_columns"])} 个</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 总体用电指标
    st.markdown('<h2 class="section-header">二、总体用电统计</h2>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    stats = data['total_stats']
    with col1:
        st.markdown(f'<div class="card"><div class="stat-label">总用电量最大值</div><div class="stat-value">{stats["max_total"]/1e8:.2f} 亿kWh</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="card"><div class="stat-label">总用电量最小值</div><div class="stat-value">{stats["min_total"]/1e8:.2f} 亿kWh</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="card"><div class="stat-label">总用电量平均值</div><div class="stat-value">{stats["avg_total"]/1e8:.2f} 亿kWh</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="card"><div class="stat-label">总用电量中位数</div><div class="stat-value">{stats["median_total"]/1e8:.2f} 亿kWh</div></div>', unsafe_allow_html=True)

    # 产业结构 饼图+柱状图（Plotly）
    st.markdown('<h2 class="section-header">三、产业用电结构分析</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    industry_df = pd.DataFrame({
        "产业": data['industry_ratio'].index,
        "占比(%)": data['industry_ratio'].values,
        "平均用电量(亿kWh)": data['industry_avg'] / 1e8
    })
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig_pie = px.pie(industry_df, values="占比(%)", names="产业", color_discrete_sequence=colors, title="各产业用电占比分布")
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig_bar = px.bar(industry_df, x="产业", y="平均用电量(亿kWh)", color_discrete_sequence=colors, title="各产业平均用电量对比")
        fig_bar.update_traces(texttemplate='%{y:.2f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 全行业月度趋势 Plotly折线图
    st.markdown('<h2 class="section-header">四、月度用电趋势（全行业）</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    month_list = [f'{i}月' for i in data['monthly_trend'].index]
    trend_df = data['monthly_trend'].copy()
    trend_df['月份'] = month_list
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=trend_df['月份'], y=trend_df['总用电量']/1e8, name='总用电量', mode='lines+markers', line_color='#FF6B6B'))
    fig_line.add_trace(go.Scatter(x=trend_df['月份'], y=trend_df['第二产业']/1e8, name='第二产业', mode='lines+markers', line_color='#4ECDC4'))
    fig_line.add_trace(go.Scatter(x=trend_df['月份'], y=trend_df['第三产业']/1e8, name='第三产业', mode='lines+markers', line_color='#45B7D1'))
    fig_line.add_trace(go.Scatter(x=trend_df['月份'], y=trend_df['居民生活用电']/1e8, name='居民生活用电', mode='lines+markers', line_color='#96CEB4'))
    fig_line.update_layout(title="2023年1-12月月度用电变化", xaxis_title="月份", yaxis_title="用电量(亿kWh)")
    st.plotly_chart(fig_line, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 关键发现
    st.markdown('<h2 class="section-header">五、关键发现</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
1. **用电结构**：第二产业为核心用电主体，工业用电占比最高；第三产业服务业用电规模紧随其后，居民生活用电占比稳定。
2. **季节性增长**：1-12月总用电量呈现明显的季节性波动，夏季（6-8月）用电峰值显著高于冬季，全年涨幅符合季节性用电规律。
3. **居民用电季节性最强**：夏季降温、冬季取暖需求拉动，居民用电季节性波动幅度远超产业用电。
4. 经济活动稳步扩张，二、三产业月度用电均保持稳定的季节性变化态势。
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== 二、区域用电分析 =====================
elif section == "区域用电分析":
    st.markdown('<h1 class="main-header">2023年1-12月区域用电分析</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">一、区域用电整体概况</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        area_df = data['area_stats'].copy()
        area_df['平均用电量(亿kWh)'] = area_df['平均用电量'] / 1e8
        fig_hbar = px.bar(area_df, y=area_df.index, x="平均用电量(亿kWh)", orientation='h', title="各区域平均用电量排名")
        fig_hbar.update_traces(texttemplate='%{x:.2f}亿kWh (%{customdata}%)', customdata=area_df['用电量占比(%)'], textposition='outside')
        st.plotly_chart(fig_hbar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        top = data['area_stats'].index[0]
        bot = data['area_stats'].index[-1]
        top_val = data['area_stats'].loc[top, '平均用电量']/1e8
        bot_val = data['area_stats'].loc[bot, '平均用电量']/1e8
        top3_pct = data['area_stats']['用电量占比(%)'].head(3).sum()
        html_block = f"""
        <div class="card">
            <p><strong>用电第一区域：{top}</strong><br>
            <span class="stat-value">{top_val:.2f} 亿kWh，占比{data["area_stats"].loc[top,"用电量占比(%)"]}%</span>
            </p>
            <hr>
            <p><strong>用电最低区域：{bot}</strong><br>
            <span class="stat-value">{bot_val:.2f} 亿kWh，占比{data["area_stats"].loc[bot,"用电量占比(%)"]}%</span>
            </p>
            <hr>
            <p><strong>前三大区域合计占比：{top3_pct:.1f}%</strong></p>
            <p>区域最高用电量差距达{((top_val/bot_val)-1)*100:.0f}%</p>
        </div>
        """
        st.markdown(html_block, unsafe_allow_html=True)

    # 全部区域月度趋势对比（Plotly多线图）
    st.markdown('<h2 class="section-header">二、全部区域月度用电趋势对比图</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    pivot = data['monthly_area_pivot']
    fig_all_line = go.Figure()
    for area in pivot.columns:
        fig_all_line.add_trace(go.Scatter(
            x=month_labels,
            y=pivot[area],
            name=area,
            mode='lines+markers'
        ))
    fig_all_line.update_layout(title="11个区域1-12月月度用电量变化对比", xaxis_title="月份", yaxis_title="月均用电量（亿kWh）")
    st.plotly_chart(fig_all_line, use_container_width=True)
    st.markdown('说明：图中每条曲线代表一个区域，可直观对比各区域月度增长速度、用电差距', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 单区域月度柱状图 Plotly
    st.markdown('<h2 class="section-header">三、单区域月度用电明细（可自选）</h2>', unsafe_allow_html=True)
    sel_area = st.selectbox('选择需要单独查看的区域', data['area_columns'])
    st.markdown('<div class="card">', unsafe_allow_html=True)
    pivot = data['monthly_area_pivot']
    area_month_data = pivot[sel_area]
    month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    single_df = pd.DataFrame({
        "月份": month_labels,
        "用电量": area_month_data.values
    })
    fig_single_bar = px.bar(single_df, x="月份", y="用电量", color_discrete_sequence=['#2E86AB'], title=f'{sel_area} 2023年1-12月月度用电量')
    fig_single_bar.update_traces(texttemplate='%{y:.2f}', textposition='outside')
    st.plotly_chart(fig_single_bar, use_container_width=True)
    # 环比增速
    growth_rate = []
    for i in range(1,12):
        g = (area_month_data.iloc[i] - area_month_data.iloc[i-1]) / area_month_data.iloc[i-1] * 100
        growth_rate.append(float(round(g,1)))
    st.write(f'月度环比增速（2→12月）：{growth_rate} %')
    st.markdown('</div>', unsafe_allow_html=True)

    # 多区域对比折线图
    st.markdown('<h2 class="section-header">四、多区域对比分析</h2>', unsafe_allow_html=True)
    select_areas = st.multiselect('多选区域进行对比', data['area_columns'], default=data['area_stats'].head(5).index.tolist())
    if select_areas:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
        pivot = data['monthly_area_pivot']
        fig_multi = go.Figure()
        for ar in select_areas:
            fig_multi.add_trace(go.Scatter(x=month_labels, y=pivot[ar], name=ar, mode='lines+markers'))
        fig_multi.update_layout(title="选中区域月度走势对比", xaxis_title="月份", yaxis_title="用电量(亿kWh)")
        st.plotly_chart(fig_multi, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 区域特征总结
    st.markdown('<h2 class="section-header">五、区域用电特征总结</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
1. **用电高度集中**：E地、F地、A地三区合计用电量占全市比重最高，工业与大型居住区集中拉高用电负荷。
2. **区域差距巨大**：核心产业区域用电量是新区的数十倍，产业与人口分布不均衡特征显著。
3. 全市所有区域月度用电均呈现明显的季节性波动，夏季用电峰值突出，冬季用电相对平稳。
4. 中心城区（C地、H地、G地）以商业服务业用电为主，月度增幅平缓；外围工业片区（A地、D地、I地）季节性增长幅度更大。
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# 页脚
st.markdown("""
<hr>
<div style="text-align:center; color:#666; margin-top:2rem;">
© 2023年1-12月某区域用电数据平台 | 数据来源：气象+分区电量统计
</div>
""", unsafe_allow_html=True)