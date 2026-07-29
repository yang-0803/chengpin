import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from datetime import datetime
import warnings
import os
import urllib.request

warnings.filterwarnings('ignore')

# ==================== 自动下载并注册中文字体 ====================
base_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(base_dir, 'NotoSansSC-Regular.ttf')

# 如果本地没有字体，自动从 Google Fonts 下载（约 2.5MB，只需下载一次）
if not os.path.exists(font_path):
    try:
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/static/NotoSansSC-Regular.ttf"
        urllib.request.urlretrieve(font_url, font_path)
    except Exception as e:
        print(f"字体自动下载失败: {e}")

# 注册字体到 matplotlib（关键：不依赖系统字体，直接加载文件）
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False
else:
    # 兜底 fallback
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

# ========== 页面配置（必须是第一个 st 命令！）==========
st.set_page_config(
    page_title="2023年1-12月用电数据展示平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 网页页面文字中文字体（页面标题/卡片不乱码）
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

# ... 后面所有业务代码完全不动 ...

# 页面配置
st.set_page_config(
    page_title="2023年1-12月用电数据展示平台",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 下面原有所有代码不动，并且**删除每张图里重复的两行plt.rcParams**

# 原有样式（保留，已搭配全局中文字体)
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

# ---------------------- 下面是你原有业务代码无需改动 ----------------------
# 数据加载、侧边栏、首页、区域分析全部保留不变

# 数据加载和预处理函数（适配1-12月数据，逻辑与原版本完全一致）
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
    
    # 区域列名映射（与原版本完全一致：宝安→A地...盐田→K地）
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
    for old_name, new_name in area_mapping.items():
        valid_data.rename(columns={old_name: new_name}, inplace=True)
    clean_area_cols = list(area_mapping.values())
    
    # 按月聚合各区域用电量透视表（适配12个月）
    monthly_area_pivot = valid_data.groupby('月份')[clean_area_cols].mean()
    monthly_area_pivot = monthly_area_pivot / 1e8  # 单位转亿kWh
    
    # 产业用电映射（与原版本完全一致）
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
    
    # 总体统计（与原版本完全一致）
    total_stats = {
        'max_total': valid_data['全社会用电总计'].max(),
        'min_total': valid_data['全社会用电总计'].min(),
        'avg_total': valid_data['全社会用电总计'].mean(),
        'median_total': valid_data['全社会用电总计'].median(),
        'std_total': valid_data['全社会用电总计'].std(),
        'record_count': len(valid_data)
    }
    
    # 区域整体统计（与原版本完全一致）
    area_stats = pd.DataFrame({
        '平均用电量': valid_data[clean_area_cols].mean(),
        '最大用电量': valid_data[clean_area_cols].max(),
        '最小用电量': valid_data[clean_area_cols].min(),
        '用电量占比(%)': (valid_data[clean_area_cols].mean() / valid_data[clean_area_cols].mean().sum() * 100).round(2)
    }).sort_values('平均用电量', ascending=False)
    
    # 全行业月度趋势（适配12个月）
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

# 侧边栏导航（与原版本完全一致）
st.sidebar.title("📊 用电数据导航")
section = st.sidebar.radio(
    "选择查看内容",
    ["首页数据概览", "区域用电分析"],
    index=0
)

# ===================== 一、首页数据概览（与原版本完全一致，仅修改文案为1-12月） =====================
if section == "首页数据概览":
    st.markdown('<h1 class="main-header">2023年1-12月用电数据展示平台</h1>', unsafe_allow_html=True)
    
    # 基础信息卡片
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

    # 产业结构饼图+柱状图（与原版本完全一致）
    st.markdown('<h2 class="section-header">三、产业用电结构分析</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 8))
        wedges, texts, autotexts = ax.pie(data['industry_ratio'].values, labels=data['industry_ratio'].index, autopct='%1.1f%%', colors=colors, startangle=90)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax.set_title('各产业用电占比分布', fontsize=14, pad=20)
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 8))
        vals = data['industry_avg'] / 1e8
        bars = ax.bar(data['industry_avg'].index, vals, color=colors, alpha=0.8)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, v, f'{v:.2f}', ha='center', va='bottom', fontweight='bold')
        ax.set_ylabel('平均用电量(亿kWh)')
        ax.set_title('各产业平均用电量对比')
        plt.xticks(rotation=45)
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # 全行业月度趋势（适配12个月）
    st.markdown('<h2 class="section-header">四、月度用电趋势（全行业）</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(14, 8))
    months = [f'{i}月' for i in data['monthly_trend'].index]
    ax.plot(months, data['monthly_trend']['总用电量']/1e8, marker='o', lw=3, label='总用电量', c='#FF6B6B')
    ax.plot(months, data['monthly_trend']['第二产业']/1e8, marker='s', lw=3, label='第二产业', c='#4ECDC4')
    ax.plot(months, data['monthly_trend']['第三产业']/1e8, marker='^', lw=3, label='第三产业', c='#45B7D1')
    ax.plot(months, data['monthly_trend']['居民生活用电']/1e8, marker='d', lw=3, label='居民生活用电', c='#96CEB4')
    ax.set_xlabel('月份')
    ax.set_ylabel('用电量(亿kWh)')
    ax.set_title('2023年1-12月月度用电变化')
    ax.legend()
    ax.grid(alpha=0.3)
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)

    # 关键发现（适配12个月数据，逻辑与原版本一致）
    st.markdown('<h2 class="section-header">五、关键发现</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
1. **用电结构**：第二产业为核心用电主体，工业用电占比最高；第三产业服务业用电规模紧随其后，居民生活用电占比稳定。
2. **季节性增长**：1-12月总用电量呈现明显的季节性波动，夏季（6-8月）用电峰值显著高于冬季，全年涨幅符合季节性用电规律。
3. **居民用电季节性最强**：夏季降温、冬季取暖需求拉动，居民用电季节性波动幅度远超产业用电。
4. 经济活动稳步扩张，二、三产业月度用电均保持稳定的季节性变化态势。
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ===================== 二、区域用电分析（与原版本完全一致，仅适配12个月） =====================
elif section == "区域用电分析":
    st.markdown('<h1 class="main-header">2023年1-12月区域用电分析</h1>', unsafe_allow_html=True)

    # 1. 区域用电整体排名（与原版本完全一致）
    st.markdown('<h2 class="section-header">一、区域用电整体概况</h2>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(12, 10))
        area_names = data['area_stats'].index
        avg_vals = data['area_stats']['平均用电量'] / 1e8
        colors = plt.cm.Set3(np.linspace(0,1,len(area_names)))
        bars = ax.barh(range(len(area_names)), avg_vals, color=colors)
        ax.set_yticks(range(len(area_names)))
        ax.set_yticklabels(area_names)
        for i, (bar, val, pct) in enumerate(zip(bars, avg_vals, data['area_stats']['用电量占比(%)'])):
            ax.text(bar.get_width(), bar.get_y()+bar.get_height()/2, f'{val:.2f}亿kWh ({pct}%)', va='center')
        ax.set_xlabel('平均用电量(亿kWh)')
        ax.set_title('各区域平均用电量排名')
        ax.grid(axis='x', alpha=0.3)
        st.pyplot(fig)
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

    # 全部区域月度用电趋势对比图（适配12个月）
    st.markdown('<h2 class="section-header">二、全部区域月度用电趋势对比图</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(16,9))
    month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    pivot = data['monthly_area_pivot']
    all_colors = plt.cm.tab20(np.linspace(0, 1, len(pivot.columns)))
    for idx, area in enumerate(pivot.columns):
        ax.plot(month_labels, pivot[area], marker='o', linewidth=2, label=area, color=all_colors[idx])
    ax.set_xlabel('月份', fontsize=12)
    ax.set_ylabel('月均用电量（亿kWh）', fontsize=12)
    ax.set_title('11个区域1-12月月度用电量变化对比', fontsize=14, weight='bold')
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    st.markdown('说明：图中每条曲线代表一个区域，可直观对比各区域月度增长速度、用电差距', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 单区域月度用电明细（适配12个月，无空隙标注）
    st.markdown('<h2 class="section-header">三、单区域月度用电明细（可自选）</h2>', unsafe_allow_html=True)
    sel_area = st.selectbox('选择需要单独查看的区域', data['area_columns'])
    st.markdown('<div class="card">', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(14,6))
    pivot = data['monthly_area_pivot']
    area_month_data = pivot[sel_area]
    month_labels = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    bars = ax.bar(month_labels, area_month_data, color='#2E86AB', alpha=0.8)
    # 标准无空隙写法：直接取bar高度，va='bottom'文字底部贴合柱顶
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{height:.2f}',
            ha='center',
            va='bottom',
            fontweight='bold'
        )
    ax.set_xlabel('月份')
    ax.set_ylabel('月均用电量（亿kWh）')
    ax.set_title(f'{sel_area} 2023年1-12月月度用电量')
    ax.grid(axis='y', alpha=0.3)
    st.pyplot(fig)
    # 计算环比增速（适配12个月：2-12月共11个增速值）
    growth_rate = []
    for i in range(1,12):
        g = (area_month_data.iloc[i] - area_month_data.iloc[i-1]) / area_month_data.iloc[i-1] * 100
        growth_rate.append(float(round(g,1)))
    st.write(f'月度环比增速（2→12月）：{growth_rate} %')
    st.markdown('</div>', unsafe_allow_html=True)

    # 多区域对比分析（适配12个月）
    st.markdown('<h2 class="section-header">四、多区域对比分析</h2>', unsafe_allow_html=True)
    select_areas = st.multiselect('多选区域进行对比', data['area_columns'], default=data['area_stats'].head(5).index.tolist())
    if select_areas:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(16,8))
        pivot = data['monthly_area_pivot']
        c_list = plt.cm.tab10(np.linspace(0,1,len(select_areas)))
        for i, ar in enumerate(select_areas):
            ax.plot(month_labels, pivot[ar], marker='o', lw=3, label=ar, color=c_list[i])
        ax.set_xlabel('月份')
        ax.set_ylabel('用电量(亿kWh)')
        ax.set_title('选中区域月度走势对比')
        ax.legend()
        ax.grid(alpha=0.3)
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # 区域特征总结（与原版本逻辑一致）
    st.markdown('<h2 class="section-header">五、区域用电特征总结</h2>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
1. **用电高度集中**：E地、F地、A地三区合计用电量占全市比重最高，工业与大型居住区集中拉高用电负荷。
2. **区域差距巨大**：核心产业区域用电量是新区的数十倍，产业与人口分布不均衡特征显著。
3. 全市所有区域月度用电均呈现明显的季节性波动，夏季用电峰值突出，冬季用电相对平稳。
4. 中心城区（C地、H地、G地）以商业服务业用电为主，月度增幅平缓；外围工业片区（A地、D地、I地）季节性增长幅度更大。
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# 页脚（与原版本完全一致）
st.markdown("""
<hr>
<div style="text-align:center; color:#666; margin-top:2rem;">
© 2023年1-12月某区域用电数据平台 | 数据来源：气象+分区电量统计
</div>
""", unsafe_allow_html=True)