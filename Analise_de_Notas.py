from dash import Dash, dcc, html, Input, Output, State, dash_table
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import base64
import io
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Inicialização do aplicativo Dash
app = Dash(__name__)

# Obtendo o ano atual
ano_atual = datetime.now().year

# Lista de opções para ano (iniciando do ano atual e indo para os anteriores)
anos = [{'label': str(year), 'value': year}
        for year in range(ano_atual, 1999, -1)]

# Lista de opções para média de aprovação
medias_aprovacao = [{'label': str(media), 'value': media}
                    for media in range(1, 11)]

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Análise de Notas dos Estudantes", style={
            'text-align': 'center', 'color': 'white'}),

    # Informações gerais
    html.Div([
        html.Label("Nome do Professor:", style={
                   'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='professor', type='text', placeholder="Nome do Professor", style={
                  'marginRight': '20px'}),
        html.Label("Instituição:", style={
                   'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='instituicao', type='text',
                  placeholder="Nome da Instituição", style={'marginRight': '20px'}),
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),

    html.Br(),
    html.Div([
        html.Label("Unidade Curricular:", style={
                   'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='disciplina', type='text',
                  placeholder="Nome da Disciplina", style={'marginRight': '20px'}),
        html.Label("Turma:", style={'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='turma', type='text', placeholder="Nome da Turma (Opcional)", style={
                  'marginRight': '20px'}),
        html.Label("Semestre:", style={
                   'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='semestre', type='text', placeholder="Semestre",
                  style={'marginRight': '20px'}),
        html.Label("Ano:", style={'color': 'white', 'marginRight': '10px'}),
        dcc.Dropdown(id='ano', options=anos, placeholder="Ano",
                     value=ano_atual, style={'width': '100px'}),
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),

    html.Br(),

    # Seleção de média de aprovação
    html.Div([
        html.Label("Média para Aprovação:", style={
                   'color': 'white', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='media-aprovacao',
            options=medias_aprovacao,
            value=6,  # Valor padrão de média para aprovação
            style={'width': '60px'},
            clearable=False
        ),
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),

    html.Br(),

    # Entrada de dados de estudantes
    html.Div([
        html.Label("Insira os nomes dos estudantes e suas notas:",
                   style={'color': 'white', 'marginRight': '10px'}),
        dcc.Input(id='input-nome', type='text', placeholder="Nome",
                  style={'marginRight': '20px', 'width': '150px'}),
        dcc.Input(id='input-nota', type='number', placeholder="Nota",
                  style={'marginRight': '20px', 'width': '80px'}),
        html.Button('Adicionar', id='add-button', n_clicks=0),
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),

    html.Br(),
    html.H3("Tabela de Notas", style={
            'text-align': 'center', 'color': 'white'}),

    dash_table.DataTable(
        id='table',
        columns=[{"name": "Nome", "id": "Nome"},
                 {"name": "Nota", "id": "Nota"}],
        data=[],
        editable=True,
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
    ),

    html.Br(),
    html.Div([
        html.Label("Ou faça o upload de um arquivo CSV:",
                   style={'color': 'white'}),
        dcc.Upload(
            id='upload-data',
            children=html.Button('Carregar CSV'),
            style={'margin': 'auto'}
        ),
        html.Div(id='output-data-upload')
    ], style={'text-align': 'center'}),

    html.Br(),
    html.Div([
        html.Button('Gerar Análise', id='generate-button', n_clicks=0),
    ], style={'text-align': 'center'}),

    dcc.Graph(id='graph'),
    html.Div(id='analysis-output',
             style={'text-align': 'center', 'color': 'white', 'font-size': '16px'}),

    html.Br(),

    # Instruções para análise
    html.H3("Instruções para Análise", style={
            'text-align': 'center', 'color': 'white'}),
    html.Div([
        html.P("A densidade de probabilidade é uma medida que mostra a probabilidade de uma variável aleatória "
               "assumir um determinado valor dentro de um intervalo. No contexto das notas, ela ajuda a visualizar "
               "como as notas estão distribuídas ao longo da escala de avaliação."),
        html.P("A curva gaussiana, também conhecida como curva normal, é uma representação gráfica que mostra a "
               "distribuição das notas em relação à média e ao desvio padrão. Ela é útil para identificar padrões, "
               "como a concentração de notas ao redor de uma média específica."),
        html.P("Indicadores de Desempenho:",
               style={'font-weight': 'bold'}),
        html.Ul([
            html.Li("Média das Notas: A média geral das notas da turma."),
            html.Li("Desvio Padrão: Mede a dispersão das notas em relação à média. Um desvio padrão baixo indica que "
                    "as notas estão próximas da média, enquanto um alto indica grande variabilidade."),
            html.Li("Curva Gaussiana: Ajuda a identificar como as notas estão distribuídas. Se a curva for muito estreita "
                    "e alta, as notas estão concentradas em torno da média. Se for larga e baixa, há maior dispersão."),
            html.Li(
                "Comparação com a Média Esperada: Verifica se a turma está alcançando a média esperada."),
            html.Li("Análise de Gap de Aprendizagem: Se houver muitos alunos com notas abaixo da média, pode ser um "
                    "indicativo de dificuldades de aprendizado ou necessidade de revisar o conteúdo."),
            html.Li(
                "Complexidade da Prova: Avalie se as questões estavam adequadas ao nível da turma."),
        ]),
    ], style={'color': 'white', 'padding': '20px', 'backgroundColor': '#444'}),
], style={'backgroundColor': '#333', 'padding': '20px'})

# Função para parsear o arquivo CSV


def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    return df

# Callback para adicionar estudantes manualmente


@app.callback(
    Output('table', 'data'),
    [Input('add-button', 'n_clicks')],
    [State('input-nome', 'value'),
     State('input-nota', 'value'),
     State('table', 'data')]
)
def add_student(n_clicks, nome, nota, rows):
    if n_clicks > 0 and nome and nota is not None:
        try:
            nota = float(nota)
            if 0 <= nota <= 10:  # Verificar se a nota está no intervalo correto
                rows.append({'Nome': nome, 'Nota': nota})
        except ValueError:
            pass  # Ignorar entradas inválidas
    return rows

# Callback para ler o arquivo CSV e atualizar a tabela


@app.callback(
    Output('table', 'data', allow_duplicate=True),
    [Input('upload-data', 'contents')],
    [State('table', 'data')],
    prevent_initial_call=True
)
def update_table_from_upload(contents, rows):
    if contents is not None:
        df = parse_contents(contents)
        if 'Nome' in df.columns and 'Nota' in df.columns:
            for index, row in df.iterrows():
                try:
                    rows.append(
                        {'Nome': row['Nome'], 'Nota': float(row['Nota'])})
                except ValueError:
                    pass  # Ignorar entradas inválidas no CSV
    return rows

# Callback para gerar o gráfico e a análise


@app.callback(
    [Output('graph', 'figure'), Output('analysis-output', 'children')],
    [Input('generate-button', 'n_clicks')],
    [State('table', 'data'),
     State('professor', 'value'),
     State('instituicao', 'value'),
     State('disciplina', 'value'),
     State('turma', 'value'),
     State('semestre', 'value'),
     State('ano', 'value'),
     State('media-aprovacao', 'value')],
    prevent_initial_call=True
)
def generate_analysis(n_clicks, data, professor, instituicao, disciplina, turma, semestre, ano, media_aprovacao):
    if n_clicks > 0 and data:
        # Verificar se a tabela possui dados válidos
        if len(data) == 0:
            return {}, "Por favor, insira os dados dos alunos para gerar a análise."

        # Converter os dados da tabela para um DataFrame
        df = pd.DataFrame(data)
        try:
            notas = df['Nota'].astype(float).tolist()
        except ValueError:
            return {}, "Erro: Algumas notas não são números válidos."

        # Calcular a média e o desvio padrão
        mu1 = np.mean(notas)
        mu2 = media_aprovacao
        sigma = np.std(notas)

        # Gerar dados para as curvas gaussianas
        x = np.linspace(0, 10, 100)
        y1 = 1/(sigma * np.sqrt(2 * np.pi)) * \
            np.exp(-(x - mu1)**2 / (2 * sigma**2))
        y2 = 1/(sigma * np.sqrt(2 * np.pi)) * \
            np.exp(-(x - mu2)**2 / (2 * sigma**2))

        # Criar gráfico interativo com melhorias
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y1, mode='lines',
                      name='Resultados da prova', fill='tozeroy', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=x, y=y2, mode='lines',
                      name='Referência', fill='tozeroy', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=notas, y=[0]*len(notas), mode='markers+text', text=df['Nome'],
                      textposition="top center", name='Notas dos alunos', marker=dict(color='red', size=10)))
        fig.add_vline(x=mu1, line=dict(color='blue', dash='dash'), annotation_text=f"Média Prova: {
                      mu1:.2f}", annotation_position="top left")
        fig.add_vline(x=mu2, line=dict(color='orange', dash='dash'),
                      annotation_text=f"Média Esperada: {mu2}", annotation_position="top right")
        fig.update_layout(title_text=f"Distribuição das Notas - {disciplina} ({turma})" if turma else f"Distribuição das Notas - {disciplina}",
                          xaxis_title="Notas", yaxis_title="Densidade de Probabilidade",
                          legend_title="Legenda", title_font_size=20,
                          autosize=True, width=1200, height=500)  # Ajuste de tamanho automático
        fig.update_xaxes(range=[0, 10])
        fig.update_yaxes(range=[0, 0.15])
        fig.update_layout(autosize=True)  # Habilitar autoscale

        # Análise do desempenho
        analysis = (f"Professor: {professor} | Instituição: {instituicao} | Unidade Curricular: {disciplina} | "
                    f"Turma: {turma if turma else 'Não especificada'} | Semestre: {
                        semestre} | Ano: {ano}.\n"
                    f"A média da prova ({mu1:.2f}) está {
            'abaixo' if mu1 < mu2 else 'dentro ou acima'} da média de aprovação esperada ({mu2}). "
            f"{'Considere revisar o conteúdo ou o formato da prova.' if mu1 < mu2 else 'Bom trabalho!'}")

        return fig, analysis
    return {}, ""


# Executar o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
