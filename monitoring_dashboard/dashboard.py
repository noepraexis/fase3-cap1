#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Visualização do Sistema de Irrigação Inteligente
=============================================================

Dashboard interativo desenvolvido com Streamlit para visualização
em tempo real dos dados do sistema de irrigação ESP32.

Funcionalidades:
- Visualização de dados dos sensores em tempo real
- Gráficos históricos de umidade, pH e nutrientes
- Controle visual do estado da irrigação
- Sistema de alertas e notificações
- Análise estatística e previsões
- Interface responsiva e intuitiva

Autor: FarmTech Solutions
Data: Janeiro 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import time
from pathlib import Path
import json

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Sistema de Irrigação Inteligente",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS customizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .alert-box {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
    }
    .alert-warning {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
    }
    .alert-info {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .status-on {
        color: #4caf50;
        font-weight: bold;
    }
    .status-off {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


class DashboardApp:
    """Classe principal do dashboard"""
    
    def __init__(self):
        self.db_path = Path("../monitoring_database/soil_monitoring.db")
        self.init_session_state()
        
    def init_session_state(self):
        """Inicializa o estado da sessão"""
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 5
        if 'selected_period' not in st.session_state:
            st.session_state.selected_period = '1h'
            
    def get_connection(self):
        """Obtém conexão com o banco de dados"""
        return sqlite3.connect(self.db_path)
        
    def load_sensor_data(self, hours=1):
        """Carrega dados dos sensores"""
        try:
            conn = self.get_connection()
            query = """
                SELECT 
                    timestamp,
                    humidity,
                    temperature,
                    ph,
                    CASE WHEN phosphorus THEN 40 ELSE 20 END as nitrogen,
                    CASE WHEN phosphorus THEN 45 ELSE 25 END as phosphorus,
                    CASE WHEN potassium THEN 35 ELSE 15 END as potassium,
                    0 as pump_state
                FROM sensor_readings
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            
            df = pd.read_sql_query(query, conn)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()
            
    def load_irrigation_events(self, hours=24):
        """Carrega eventos de irrigação"""
        try:
            conn = self.get_connection()
            query = """
                SELECT 
                    timestamp as event_time,
                    event_type,
                    duration_seconds,
                    trigger_source as trigger_reason
                FROM irrigation_events
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(hours)
            
            df = pd.read_sql_query(query, conn)
            df['event_time'] = pd.to_datetime(df['event_time'])
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar eventos: {e}")
            return pd.DataFrame()
            
    def load_alerts(self, hours=24):
        """Carrega alertas do sistema"""
        try:
            conn = self.get_connection()
            query = """
                SELECT 
                    timestamp as alert_time,
                    alert_type,
                    CASE 
                        WHEN alert_type LIKE '%temperature%' THEN 'temperature'
                        WHEN alert_type LIKE '%humidity%' THEN 'humidity'
                        WHEN alert_type LIKE '%ph%' THEN 'ph'
                        ELSE 'sensor'
                    END as sensor_type,
                    sensor_value,
                    threshold_value,
                    message
                FROM alerts
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT 20
            """.format(hours)
            
            df = pd.read_sql_query(query, conn)
            df['alert_time'] = pd.to_datetime(df['alert_time'])
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erro ao carregar alertas: {e}")
            return pd.DataFrame()
            
    def load_system_stats(self):
        """Carrega estatísticas do sistema"""
        try:
            conn = self.get_connection()
            query = """
                SELECT 
                    datetime('now') as stats_time,
                    COUNT(*) as total_readings,
                    AVG(humidity) as avg_humidity,
                    AVG(temperature) as avg_temperature,
                    AVG(ph) as avg_ph,
                    (SELECT COUNT(*) FROM irrigation_events WHERE event_type = 'start') as irrigation_count,
                    (SELECT COALESCE(SUM(duration_seconds)/60.0, 0) FROM irrigation_events) as total_irrigation_time
                FROM sensor_readings
                WHERE timestamp > datetime('now', '-24 hours')
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if not df.empty:
                return df.iloc[0].to_dict()
            return None
        except Exception as e:
            st.error(f"Erro ao carregar estatísticas: {e}")
            return None
            
    def create_gauge_chart(self, value, title, min_val, max_val, 
                          optimal_range=None, unit=""):
        """Cria um gráfico de medidor (gauge)"""
        if optimal_range:
            steps = [
                {'range': [min_val, optimal_range[0]], 'color': "lightgray"},
                {'range': optimal_range, 'color': "lightgreen"},
                {'range': [optimal_range[1], max_val], 'color': "lightgray"}
            ]
        else:
            steps = [{'range': [min_val, max_val], 'color': "lightgray"}]
            
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 20}},
            number={'suffix': unit, 'font': {'size': 24}},
            gauge={
                'axis': {'range': [min_val, max_val], 'tickwidth': 1, 
                        'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': steps,
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.9
                }
            }
        ))
        
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        return fig
        
    def create_time_series_chart(self, df, columns, title):
        """Cria gráfico de série temporal"""
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        for i, col in enumerate(columns):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df[col],
                    mode='lines+markers',
                    name=col.replace('_', ' ').title(),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=4)
                ))
                
        fig.update_layout(
            title=title,
            xaxis_title="Tempo",
            yaxis_title="Valor",
            hovermode='x unified',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxis(rangeslider_visible=True)
        return fig
        
    def create_nutrient_bar_chart(self, n_val, p_val, k_val):
        """Cria gráfico de barras para nutrientes"""
        nutrients = ['Nitrogênio', 'Fósforo', 'Potássio']
        values = [n_val, p_val, k_val]
        colors = ['#4CAF50', '#FF9800', '#2196F3']
        
        fig = go.Figure(data=[
            go.Bar(
                x=nutrients,
                y=values,
                text=[f'{v:.1f}' for v in values],
                textposition='auto',
                marker_color=colors
            )
        ])
        
        fig.update_layout(
            title="Níveis de Nutrientes (NPK)",
            yaxis_title="Concentração",
            showlegend=False,
            height=300
        )
        
        return fig
        
    def render_sidebar(self):
        """Renderiza a barra lateral"""
        st.sidebar.markdown("## ⚙️ Configurações")
        
        # Período de visualização
        period_options = {
            '1h': 'Última hora',
            '6h': 'Últimas 6 horas',
            '24h': 'Último dia',
            '7d': 'Última semana',
            '30d': 'Último mês'
        }
        
        selected_period = st.sidebar.selectbox(
            "Período de visualização",
            options=list(period_options.keys()),
            format_func=lambda x: period_options[x],
            index=0
        )
        
        # Converte período para horas
        period_hours = {
            '1h': 1,
            '6h': 6,
            '24h': 24,
            '7d': 168,
            '30d': 720
        }
        
        # Auto-refresh
        st.sidebar.markdown("### 🔄 Atualização Automática")
        auto_refresh = st.sidebar.checkbox("Ativar auto-refresh", 
                                          value=st.session_state.auto_refresh)
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Intervalo (segundos)",
                min_value=5,
                max_value=60,
                value=st.session_state.refresh_interval,
                step=5
            )
            st.session_state.refresh_interval = refresh_interval
            
        st.session_state.auto_refresh = auto_refresh
        
        # Informações do sistema
        st.sidebar.markdown("### 📊 Informações do Sistema")
        stats = self.load_system_stats()
        if stats:
            st.sidebar.metric("Total de Leituras", f"{stats['total_readings']:,}")
            st.sidebar.metric("Irrigações Hoje", stats['irrigation_count'])
            st.sidebar.metric("Tempo Total Irrigação", 
                            f"{stats['total_irrigation_time']:.1f} min")
            
        return period_hours[selected_period]
        
    def render_header(self):
        """Renderiza o cabeçalho"""
        st.markdown('<h1 class="main-header">🌱 Sistema de Irrigação Inteligente</h1>', 
                   unsafe_allow_html=True)
        st.markdown("---")
        
        # Informações de última atualização
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.info(f"📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        with col2:
            if st.session_state.auto_refresh:
                st.success(f"🔄 Auto-refresh ativo ({st.session_state.refresh_interval}s)")
            else:
                st.warning("⏸️ Auto-refresh desativado")
        with col3:
            if st.button("🔄 Atualizar Agora"):
                st.rerun()
                
    def render_current_status(self, df):
        """Renderiza status atual dos sensores"""
        st.markdown("## 📊 Status Atual")
        
        if df.empty:
            st.warning("Nenhum dado disponível")
            return
            
        # Obtém última leitura
        latest = df.iloc[0]
        
        # Cria colunas para os medidores
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fig = self.create_gauge_chart(
                latest['humidity'], 
                "Umidade do Solo", 
                0, 100, 
                optimal_range=[40, 60],
                unit="%"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            fig = self.create_gauge_chart(
                latest['temperature'], 
                "Temperatura", 
                0, 50, 
                optimal_range=[20, 30],
                unit="°C"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col3:
            fig = self.create_gauge_chart(
                latest['ph_value'], 
                "pH do Solo", 
                0, 14, 
                optimal_range=[6, 7],
                unit=""
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col4:
            # Status da bomba
            pump_status = "LIGADA" if latest['pump_state'] else "DESLIGADA"
            pump_color = "status-on" if latest['pump_state'] else "status-off"
            
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <h3>💧 Bomba de Irrigação</h3>
                <h1 class="{pump_color}">{pump_status}</h1>
                <p>Última verificação: {latest['timestamp'].strftime('%H:%M:%S')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Gráfico de nutrientes
        st.markdown("### 🧪 Análise de Nutrientes")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Nitrogênio (N)", f"{latest['nitrogen']:.1f}", 
                     delta=f"{latest['nitrogen'] - 30:.1f}")
            st.metric("Fósforo (P)", f"{latest['phosphorus']:.1f}", 
                     delta=f"{latest['phosphorus'] - 40:.1f}")
            st.metric("Potássio (K)", f"{latest['potassium']:.1f}", 
                     delta=f"{latest['potassium'] - 35:.1f}")
            
        with col2:
            fig = self.create_nutrient_bar_chart(
                latest['nitrogen'],
                latest['phosphorus'],
                latest['potassium']
            )
            st.plotly_chart(fig, use_container_width=True)
            
    def render_historical_data(self, df):
        """Renderiza dados históricos"""
        st.markdown("## 📈 Dados Históricos")
        
        if df.empty:
            st.warning("Nenhum dado histórico disponível")
            return
            
        # Tabs para diferentes visualizações
        tab1, tab2, tab3 = st.tabs(["Sensores Ambientais", "Nutrientes", "Irrigação"])
        
        with tab1:
            # Gráfico de umidade e temperatura
            fig1 = self.create_time_series_chart(
                df, 
                ['humidity', 'temperature'], 
                "Umidade e Temperatura ao Longo do Tempo"
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Gráfico de pH
            fig2 = self.create_time_series_chart(
                df, 
                ['ph_value'], 
                "pH do Solo ao Longo do Tempo"
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        with tab2:
            # Gráfico de nutrientes
            fig3 = self.create_time_series_chart(
                df, 
                ['nitrogen', 'phosphorus', 'potassium'], 
                "Níveis de Nutrientes (NPK) ao Longo do Tempo"
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Análise de correlação
            if len(df) > 10:
                st.markdown("### 🔍 Análise de Correlação")
                corr_cols = ['humidity', 'temperature', 'ph_value', 
                            'nitrogen', 'phosphorus', 'potassium']
                corr_data = df[corr_cols].corr()
                
                fig_corr = px.imshow(
                    corr_data,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale='RdBu',
                    title="Matriz de Correlação entre Sensores"
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                
        with tab3:
            # Estado da bomba ao longo do tempo
            pump_df = df.copy()
            pump_df['pump_state'] = pump_df['pump_state'].astype(int)
            
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=pump_df['timestamp'],
                y=pump_df['pump_state'],
                mode='lines',
                line=dict(shape='hv', color='blue', width=2),
                fill='tozeroy',
                name='Estado da Bomba'
            ))
            
            fig4.update_layout(
                title="Estado da Bomba de Irrigação",
                xaxis_title="Tempo",
                yaxis_title="Estado",
                yaxis=dict(
                    tickmode='array',
                    tickvals=[0, 1],
                    ticktext=['Desligada', 'Ligada']
                ),
                height=300
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Eventos de irrigação
            events_df = self.load_irrigation_events(24)
            if not events_df.empty:
                st.markdown("### 💧 Eventos de Irrigação")
                
                # Resumo
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_events = len(events_df)
                    st.metric("Total de Eventos", total_events)
                with col2:
                    total_duration = events_df['duration_seconds'].sum() / 60
                    st.metric("Tempo Total", f"{total_duration:.1f} min")
                with col3:
                    avg_duration = events_df['duration_seconds'].mean()
                    st.metric("Duração Média", f"{avg_duration:.0f} seg")
                    
                # Tabela de eventos
                st.dataframe(
                    events_df[['event_time', 'event_type', 'duration_seconds', 
                              'trigger_reason']].head(10),
                    use_container_width=True
                )
                
    def render_alerts(self):
        """Renderiza alertas do sistema"""
        st.markdown("## 🚨 Alertas e Notificações")
        
        alerts_df = self.load_alerts(24)
        
        if alerts_df.empty:
            st.success("✅ Nenhum alerta ativo no momento")
            return
            
        # Contadores de alertas
        col1, col2, col3 = st.columns(3)
        
        critical_count = len(alerts_df[alerts_df['alert_type'] == 'critical'])
        warning_count = len(alerts_df[alerts_df['alert_type'] == 'warning'])
        info_count = len(alerts_df[alerts_df['alert_type'] == 'info'])
        
        with col1:
            st.metric("🔴 Críticos", critical_count)
        with col2:
            st.metric("🟡 Avisos", warning_count)
        with col3:
            st.metric("🔵 Informativos", info_count)
            
        # Lista de alertas
        st.markdown("### 📋 Alertas Recentes")
        
        for _, alert in alerts_df.head(10).iterrows():
            alert_class = f"alert-{alert['alert_type']}"
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                alert['alert_type'], "⚪"
            )
            
            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <strong>{icon} {alert['sensor_type'].upper()}</strong> - 
                {alert['alert_time'].strftime('%d/%m %H:%M')}
                <br>
                {alert['message']}
                <br>
                <small>Valor: {alert['sensor_value']:.2f} | 
                Limite: {alert['threshold_value']:.2f}</small>
            </div>
            """, unsafe_allow_html=True)
            
    def render_analytics(self, df):
        """Renderiza análises e previsões"""
        st.markdown("## 🔮 Análise e Previsões")
        
        if df.empty or len(df) < 10:
            st.info("Dados insuficientes para análise preditiva")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Estatísticas do Período")
            
            # Estatísticas descritivas
            stats_df = df[['humidity', 'temperature', 'ph_value']].describe()
            st.dataframe(stats_df, use_container_width=True)
            
            # Tendências
            st.markdown("### 📈 Tendências Observadas")
            
            # Calcula tendências simples
            humidity_trend = np.polyfit(range(len(df)), df['humidity'], 1)[0]
            temp_trend = np.polyfit(range(len(df)), df['temperature'], 1)[0]
            ph_trend = np.polyfit(range(len(df)), df['ph_value'], 1)[0]
            
            trends = {
                "Umidade": "↑ Aumentando" if humidity_trend > 0 else "↓ Diminuindo",
                "Temperatura": "↑ Aumentando" if temp_trend > 0 else "↓ Diminuindo",
                "pH": "↑ Aumentando" if ph_trend > 0 else "↓ Diminuindo"
            }
            
            for sensor, trend in trends.items():
                st.write(f"**{sensor}**: {trend}")
                
        with col2:
            st.markdown("### 🎯 Recomendações")
            
            # Análise das condições atuais
            latest = df.iloc[0]
            recommendations = []
            
            if latest['humidity'] < 40:
                recommendations.append("💧 Umidade baixa - considere aumentar irrigação")
            elif latest['humidity'] > 60:
                recommendations.append("💦 Umidade alta - reduza a irrigação")
                
            if latest['ph_value'] < 6:
                recommendations.append("🧪 pH ácido - considere correção com calcário")
            elif latest['ph_value'] > 7:
                recommendations.append("🧪 pH alcalino - considere correção com sulfato")
                
            if latest['nitrogen'] < 20:
                recommendations.append("🌱 Nitrogênio baixo - aplique fertilizante nitrogenado")
                
            if latest['phosphorus'] < 30:
                recommendations.append("🌿 Fósforo baixo - aplique fertilizante fosfatado")
                
            if latest['potassium'] < 25:
                recommendations.append("🍃 Potássio baixo - aplique fertilizante potássico")
                
            if recommendations:
                for rec in recommendations:
                    st.info(rec)
            else:
                st.success("✅ Todas as condições estão dentro dos parâmetros ideais!")
                
            # Previsão de próxima irrigação
            st.markdown("### ⏰ Previsão de Irrigação")
            
            # Estimativa simples baseada na taxa de perda de umidade
            if len(df) > 2:
                humidity_rate = (df.iloc[0]['humidity'] - df.iloc[-1]['humidity']) / len(df)
                if humidity_rate < 0:  # Umidade diminuindo
                    hours_to_irrigation = (latest['humidity'] - 40) / abs(humidity_rate)
                    st.write(f"Próxima irrigação estimada em: **{hours_to_irrigation:.1f} horas**")
                else:
                    st.write("Umidade estável ou aumentando - irrigação não necessária")
                    
    def run(self):
        """Executa o dashboard"""
        # Renderiza sidebar e obtém período selecionado
        period_hours = self.render_sidebar()
        
        # Renderiza cabeçalho
        self.render_header()
        
        # Carrega dados
        df = self.load_sensor_data(period_hours)
        
        # Renderiza seções
        self.render_current_status(df)
        st.markdown("---")
        
        self.render_historical_data(df)
        st.markdown("---")
        
        self.render_alerts()
        st.markdown("---")
        
        self.render_analytics(df)
        
        # Auto-refresh
        if st.session_state.auto_refresh:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()


def main():
    """Função principal"""
    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()