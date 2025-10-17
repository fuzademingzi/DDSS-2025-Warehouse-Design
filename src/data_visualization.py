# -*- coding:utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page setting
st.set_page_config(page_title="Stock level analyse", page_icon="📦", layout="wide")
st.title("📊 Warehouse inventory data analysis dashboard")


df = pd.read_csv('./data/raw_data.csv')
df.fillna(0, inplace=True)
df['code'] = df['code'].astype(str).str.replace(',', '')

# Sidebar filter
st.sidebar.header("🔍 Data Filters")

# Volume Filter
vol_min, vol_max = st.sidebar.slider(
    "Volume range (m³)",
    float(df['volum (m3)'].min()),
    float(df['volum (m3)'].quantile(1)),
    (float(df['volum (m3)'].min()), float(df['volum (m3)'].quantile(1)))
)

# Weight Filter
weight_min, weight_max = st.sidebar.slider(
    "Weight range (kg)",
    float(df['weight (kg)'].min()),
    float(df['weight (kg)'].quantile(1)),
    (float(df['weight (kg)'].min()), float(df['weight (kg)'].quantile(1)))
)

# Stock level filter
inventory_min, inventory_max = st.sidebar.slider(
    "Inventory range",
    int(df['inventory (units)'].min()),
    int(df['inventory (units)'].max()),
    (int(df['inventory (units)'].min()), int(df['inventory (units)'].max()))
)

# apply the filter
filtered_df = df[
    (df['volum (m3)'] >= vol_min) & (df['volum (m3)'] <= vol_max) &
    (df['weight (kg)'] >= weight_min) & (df['weight (kg)'] <= weight_max) &
    (df['inventory (units)'] >= inventory_min) & (df['inventory (units)'] <= inventory_max)
]

st.sidebar.metric("Quantity of products after filtering", f"{len(filtered_df):,}")

# Main page
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📐 3D size distribution", 
    "📦 Inventory analysis", 
    "⚖️ Weight-volume relationship", 
    "📏 Volume distribution",
    "⏲️ Weight distribution",
    "🚚 Total Volume"
])

with tab1:
    st.header("3D size distribution")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Legend Settings")
        color_by = st.selectbox(
            "Color representation",
            ["weight (kg)", "inventory (units)", "volum (m3)"],
            key="color_3d"
        )
        size_by = st.selectbox(
            "Point size representation",
            ["inventory (units)", "weight (kg)", "volum (m3)"],
            key="size_3d"
        )
        
        # Size limit
        max_length = st.number_input("Maximum length limit (cm)", 1, 500, 100, key="max_len")
        max_width = st.number_input("Maximum width limit (cm)", 3, 300, 60, key="max_width")
        max_height = st.number_input("Maximum height limit (cm)", 2, 200, 40, key="max_height")
    
    with col1:
        # filter the extreme values
        plot_df = filtered_df[
            (filtered_df['lenght (cm)'] <= max_length) &
            (filtered_df['width (cm)'] <= max_width) &
            (filtered_df['height (cm)'] <= max_height)
        ]
        
        # create the 3d scatter
        fig = px.scatter_3d(
            plot_df,
            x='lenght (cm)',
            y='width (cm)',
            z='height (cm)',
            color=color_by,
            size=size_by,
            size_max=30,
            hover_data=['code', 'volum (m3)', 'weight (kg)', 'inventory (units)'],
            title=f'3D size distribution<br><sub>Color: {color_by} | Size: {size_by}</sub>',
            color_continuous_scale='viridis'
        )
        
        # update the distribution
        fig.update_layout(
            scene=dict(
                xaxis_title='lenght (cm)',
                yaxis_title='width (cm)',
                zaxis_title='height (cm)'
            ),
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"Displaying {len(plot_df)} products（Extreme sizes filtered）")

with tab2:
    st.header("Inventory quantity distribution analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pareto analisis
        inventory_sorted = filtered_df.sort_values('inventory (units)', ascending=False)
        inventory_sorted['cumulative_percent'] = inventory_sorted['inventory (units)'].cumsum() / inventory_sorted['inventory (units)'].sum() * 100
        inventory_sorted['rank'] = range(1, len(inventory_sorted) + 1)
        
        # add the Pareto chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add Histogram
        fig.add_trace(
            go.Bar(
                x=inventory_sorted['rank'],
                y=inventory_sorted['inventory (units)'],
                name="Quantity",
                marker_color='skyblue',
                opacity=0.7
            ),
            secondary_y=False,
        )
        
        # Add accumulated percentage line
        fig.add_trace(
            go.Scatter(
                x=inventory_sorted['rank'],
                y=inventory_sorted['cumulative_percent'],
                name="Cumulative percentage",
                line=dict(color='red', width=3),
                mode='lines'
            ),
            secondary_y=True,
        )
        
        # Add a reference line
        fig.add_hline(y=80, line_dash="dash", line_color="green", secondary_y=True,
                     annotation_text="80%", annotation_position="right")
        fig.add_hline(y=95, line_dash="dash", line_color="orange", secondary_y=True,
                     annotation_text="95%", annotation_position="right")
        
        # Update the layout
        fig.update_layout(
            title="Stock Pareto Analysis (ABC Classification)",
            xaxis_title="Product serial number (in descending order by inventory)",
            height=500
        )
        
        fig.update_yaxes(title_text="Quantity", secondary_y=False)
        fig.update_yaxes(title_text="Cumulative percentage (%)", secondary_y=True, range=[0, 100])
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # ABC Classification
        total_inventory = inventory_sorted['inventory (units)'].sum()
        a_class = inventory_sorted[inventory_sorted['cumulative_percent'] <= 80]
        b_class = inventory_sorted[(inventory_sorted['cumulative_percent'] > 80) & 
                                 (inventory_sorted['cumulative_percent'] <= 95)]
        c_class = inventory_sorted[inventory_sorted['cumulative_percent'] > 95]
        
        st.subheader("ABC Classification")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Category A", 
                     f"{len(a_class)}", 
                     f"{a_class['inventory (units)'].sum()/total_inventory*100:.1f}%")
        with col_b:
            st.metric("Category B", 
                     f"{len(b_class)}", 
                     f"{b_class['inventory (units)'].sum()/total_inventory*100:.1f}%")
        with col_c:
            st.metric("Category C", 
                     f"{len(c_class)}", 
                     f"{c_class['inventory (units)'].sum()/total_inventory*100:.1f}%")
        
        # Stock level distribution
        fig2 = px.histogram(
            filtered_df,
            x='inventory (units)',
            nbins=30,
            title='Inventory quantity distribution histogram',
            color_discrete_sequence=['lightgreen']
        )
        
        fig2.update_layout(
            xaxis_title='Quantity',
            yaxis_title='Number of SKU',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    with st.expander("🔠 Category details"):
        col3, col4, col5 = st.columns(3)
        with col3:
            st.write('Category A')
            st.dataframe(a_class[['code', 'weight (kg)', 'volum (m3)', 'inventory (units)', 'rank']], hide_index=True)
            st.write(f"Total number: {len(a_class)}")
        with col4:
            st.write('Category B')
            st.dataframe(b_class[['code', 'weight (kg)', 'volum (m3)', 'inventory (units)', 'rank']], hide_index=True)
            st.write(f"Total number: {len(b_class)}")
        with col5:
            st.write('Category C')
            st.dataframe(c_class[['code', 'weight (kg)', 'volum (m3)', 'inventory (units)', 'rank']], hide_index=True)
            st.write(f"Total number: {len(c_class)}")

with tab3:
    st.header("Weight-volume relationship")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Analysis Settings")
        show_trend = st.checkbox("Show Trend Line", value=True, key="trend")
        log_scale = st.checkbox("Logarithmic coordinates", value=True, key="log")
        color_scheme = st.selectbox(
            "Color scheme",
            ["viridis", "plasma", "inferno", "magma", "cividis"],
            key="color_scheme"
        )
    
    with col1:
        # Add scatter
        fig = px.scatter(
            filtered_df,
            x='volum (m3)',
            y='weight (kg)',
            color='inventory (units)',
            size='inventory (units)',
            hover_data=['code', 'lenght (cm)', 'width (cm)', 'height (cm)'],
            title='Weight-volume relationship',
            color_continuous_scale=color_scheme
        )
        
        if show_trend:
            # Trend line
            z = np.polyfit(filtered_df['volum (m3)'], filtered_df['weight (kg)'], 1)
            p = np.poly1d(z)
            x_trend = np.linspace(filtered_df['volum (m3)'].min(), filtered_df['volum (m3)'].max(), 100)
            
            fig.add_trace(
                go.Scatter(
                    x=x_trend,
                    y=p(x_trend),
                    mode='lines',
                    line=dict(color='red', dash='dash'),
                    name='Trend line'
                )
            )
        
        if log_scale:
            fig.update_xaxes(type="log")
            fig.update_yaxes(type="log")
        
        fig.update_layout(
            xaxis_title='Volume (m³)',
            yaxis_title='Weight (kg)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlation
    corr = filtered_df['volum (m3)'].corr(filtered_df['weight (kg)'])
    st.metric("Weight-volume correlation coefficient", f"{corr:.3f}")

with tab4:
    st.header("Volume distribution analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume distribution
        fig1 = px.histogram(
            filtered_df,
            x='volum (m3)',
            nbins=50,
            title='Product volume distribution histogram',
            color_discrete_sequence=['lightcoral'],
            opacity=0.7
        )
        
        # Add the mean & median line
        mean_vol = filtered_df['volum (m3)'].mean()
        median_vol = filtered_df['volum (m3)'].median()
        
        fig1.add_vline(x=mean_vol, line_dash="dash", line_color="red", 
                      annotation_text=f"Mean: {mean_vol:.4f}")
        fig1.add_vline(x=median_vol, line_dash="dash", line_color="blue",
                      annotation_text=f"Median: {median_vol:.4f}")
        
        fig1.update_layout(
            xaxis_title='Volume (m³)',
            yaxis_title='Quantity',
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Volume box plot
        fig2 = px.box(
            filtered_df,
            y='volum (m3)',
            title='Volume distribution box plot',
            color_discrete_sequence=['orange']
        )
        
        fig2.update_layout(
            yaxis_title='Volume (m³)',
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # Volume summary
    st.subheader("Volume Statistics Summary")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("Average volume", f"{filtered_df['volum (m3)'].mean():.4f} m³")
    with col_stat2:
        st.metric("Median volume", f"{filtered_df['volum (m3)'].median():.4f} m³")
    with col_stat3:
        st.metric("Volume standard deviation", f"{filtered_df['volum (m3)'].std():.4f} m³")
    with col_stat4:
        st.metric("Volume range", f"{filtered_df['volum (m3)'].min():.4f} - {filtered_df['volum (m3)'].max():.4f} m³")

with tab5:
    st.header("Weight distribution analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Weight distribution
        fig1 = px.histogram(
            filtered_df,
            x='weight (kg)',
            nbins=50,
            title='Product volume distribution histogram',
            color_discrete_sequence=['lightgreen'],
            opacity=0.7
        )
        
        # Add the mean & median line
        mean_vol = filtered_df['weight (kg)'].mean()
        median_vol = filtered_df['weight (kg)'].median()
        
        fig1.add_vline(x=mean_vol, line_dash="dash", line_color="green", 
                      annotation_text=f"Mean: {mean_vol:.4f}")
        fig1.add_vline(x=median_vol, line_dash="dash", line_color="blue",
                      annotation_text=f"Median: {median_vol:.4f}")
        
        fig1.update_layout(
            xaxis_title='Weight (kg)',
            yaxis_title='Quantity',
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Weight box plot
        fig2 = px.box(
            filtered_df,
            y='weight (kg)',
            title='Weight distribution box plot',
            color_discrete_sequence=['purple']
        )
        
        fig2.update_layout(
            yaxis_title='Weight (kg)',
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # Weight Summary
    st.subheader("Weight Statistics Summary")
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        st.metric("Average Weight", f"{filtered_df['weight (kg)'].mean():.4f} kg")
    with col_stat2:
        st.metric("Median Weight", f"{filtered_df['weight (kg)'].median():.4f} kg")
    with col_stat3:
        st.metric("Weight standard deviation", f"{filtered_df['weight (kg)'].std():.4f} kg")
    with col_stat4:
        st.metric("Weight range", f"{filtered_df['weight (kg)'].min():.4f} - {filtered_df['weight (kg)'].max():.4f} kg")

with tab6:
    st.header("Total Storage Volume Analysis")
    
    # Calculate total storage volume (unit volume × inventory quantity)
    filtered_df['total_storage_volume'] = filtered_df['volum (m3)'] * filtered_df['inventory (units)']
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("Analysis Settings")
        chart_type = st.selectbox(
            "Select Chart Type",
            ["Pareto Chart", "Treemap"],
            key="storage_chart"
        )
        top_n = st.slider("Show Top N Products", 10, 1000, 20, key="top_n")
        
    with col1:
        # Sort by total storage volume
        storage_sorted = filtered_df.sort_values('total_storage_volume', ascending=False)
        storage_sorted['cumulative_percent'] = storage_sorted['total_storage_volume'].cumsum() / storage_sorted['total_storage_volume'].sum() * 100
        storage_sorted['rank'] = range(1, len(storage_sorted) + 1)
        
        if chart_type == "Pareto Chart":
            # Pareto chart for total storage volume
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Bar(
                    x=storage_sorted['rank'],
                    y=storage_sorted['total_storage_volume'],
                    name="Total Storage Volume",
                    marker_color='lightblue',
                    opacity=0.7
                ),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(
                    x=storage_sorted['rank'],
                    y=storage_sorted['cumulative_percent'],
                    name="Cumulative %",
                    line=dict(color='red', width=3),
                    mode='lines'
                ),
                secondary_y=True,
            )
            
            # Add reference lines for 80/20 analysis
            fig.add_hline(y=80, line_dash="dash", line_color="green", secondary_y=True,
                         annotation_text="80%", annotation_position="right")
            fig.add_hline(y=95, line_dash="dash", line_color="orange", secondary_y=True,
                         annotation_text="95%", annotation_position="right")
            
            fig.update_layout(
                title="Total Storage Volume Pareto Analysis",
                xaxis_title="Product Rank (by Total Storage Volume)",
                height=500
            )
            
            fig.update_yaxes(title_text="Total Storage Volume (m³)", secondary_y=False)
            fig.update_yaxes(title_text="Cumulative Percentage (%)", secondary_y=True, range=[0, 100])
            
        elif chart_type == "Treemap":
            # Treemap for visual space distribution
            top_data = storage_sorted.head(top_n)
            percentage = top_data['cumulative_percent'].iloc[-1]
            fig = px.treemap(
                top_data,
                path=[px.Constant("All Products"), 'code'],
                values='total_storage_volume',
                color='total_storage_volume',
                color_continuous_scale='Blues',
                title=f'<b>Total Storage Volume Distribution Treemap (Top {top_n})</b><br><span style="font-size: 12px; color: gray">These {top_n} products account for {percentage:.1f}% of total storage volume</span>',
                hover_data=['volum (m3)', 'inventory (units)']
            )
            fig.update_layout(height=500)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics for storage volume analysis
    st.subheader("Key Storage Metrics")
    col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
    
    total_volume = storage_sorted['total_storage_volume'].sum()
    top_20_percent = storage_sorted.head(int(len(storage_sorted)*0.2))['total_storage_volume'].sum()
    
    with col_metrics1:
        st.metric("Total Storage Volume Required", f"{total_volume:.2f} m³")
    with col_metrics2:
        st.metric("Top 20% Products Share", f"{(top_20_percent/total_volume*100):.1f}%")
    with col_metrics3:
        st.metric("Avg Storage per Product", f"{storage_sorted['total_storage_volume'].mean():.2f} m³")
    with col_metrics4:
        st.metric("Largest Product Volume", f"{storage_sorted.iloc[0]['total_storage_volume']:.2f} m³")
    

# Data Overview
with st.expander("📋 Data Overview"):
    st.dataframe(filtered_df, hide_index=True)
    st.write(f"Total number of records: {len(filtered_df)}")
    st.write(f"Data Dimensions: {filtered_df.shape}")

st.sidebar.info("💡 Tip: Use filters to explore a different range of product characteristics")