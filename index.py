import dash
import dash_core_components as dcc 
import dash_html_components as html
from dash_html_components.H1 import H1
import plotly.express as px
import pandas as pd 
from dash.dependencies import Input,Output
import pymysql
import dash_table
from stop_words import get_stop_words
#### montar el word cloud
from wordcloud import WordCloud
import base64
from io import BytesIO


#######################################
#Conexion a la base de datos mysql 
connection = pymysql.connect(
  host="localhost",
  user="root",
  password="",
  db="shd"  
)

#query a la base de datos para gtardar en un data frame
select_stmt = (
          "select DATE_FORMAT(fecha_tweeter, '%d/%m/%y') Fecha_tweeter, sum(if(eval_Sentimiento_resul=1,1,0)) Cantidad_positivos, sum(if(eval_Sentimiento_resul=-1,1,0)) Cantidad_negativos, sum(if(eval_Sentimiento_resul=0,1,0)) Cantidad_neutros"
          " from shd.tweets where id_tweeter <> 1" 
          " and DATE_FORMAT(fecha_tweeter, '%d/%m/%y') between DATE_FORMAT(now(), '%d/%m/%y') and DATE_FORMAT((NOW() - INTERVAL 5 DAY), '%d/%m/%y') "
          " group by DATE_FORMAT(fecha_tweeter, '%d/%m/%y') order by 1"                    
        )
sqlSt = "SELECT * FROM shd.tweets"

df = pd.read_sql(sqlSt,connection)

def nombrado(text):
    if text == '0':
        return 'Neutro'
    elif text == '1':
        return 'Positivo'
    elif text == '-1':
        return 'Negativo'
    else :
        return '0'

df['Sentimiento'] = df['eval_Sentimiento_resul'].apply(nombrado)
df['SentimientoNum'] = 1
df_neg = df[df['eval_Sentimiento_resul'] == '-1']
df_neg = df_neg.drop(['id_tweeter','ubicacion','texto_tweet_limpio','eval_Sentimiento','eval_Sentimiento_resul','fecha_registro','SentimientoNum','Sentimiento'], axis=1)

#print(df_neg)

select_stmt = (
          "select DATE_FORMAT(fecha_tweeter, '%d/%m/%y') Fecha_tweeter, sum(if(eval_Sentimiento_resul=1,1,0)) Cantidad_positivos, sum(if(eval_Sentimiento_resul=-1,1,0)) Cantidad_negativos, sum(if(eval_Sentimiento_resul=0,1,0)) Cantidad_neutros"
          " from shd.tweets  "
          #" where  DATE_FORMAT(fecha_tweeter, '%d/%m/%y') = DATE_FORMAT(now(), '%d/%m/%y') "
          #"or DATE_FORMAT(fecha_tweeter, '%d/%m/%y') = DATE_FORMAT((NOW() - INTERVAL 1 day), '%d/%m/%y') "
          #"or DATE_FORMAT(fecha_tweeter, '%d/%m/%y') = DATE_FORMAT((NOW() - INTERVAL 2 day), '%d/%m/%y') "
          #"or DATE_FORMAT(fecha_tweeter, '%d/%m/%y') = DATE_FORMAT((NOW() - INTERVAL 3 day), '%d/%m/%y') "
          #"or DATE_FORMAT(fecha_tweeter, '%d/%m/%y') = DATE_FORMAT((NOW() - INTERVAL 4 day), '%d/%m/%y') "

          " group by DATE_FORMAT(fecha_tweeter, '%d/%m/%y') order by Fecha_tweeter DESC"                    
        )
result_dF = pd.read_sql(select_stmt,connection)
#result_dF = result_dF.set_index('Fecha_tweeter')
#print(result_dF)

#print(df_negativo)

#cerrar la conexion a la base de datos

#crear wordcloud
palabras_irrelevantes = get_stop_words('spanish')
text = ' '.join(df.texto_tweet_limpio)

wordcloud = WordCloud(width=1024, height=800, colormap='Blues', min_font_size=14,stopwords=palabras_irrelevantes).generate(text)
wc_img = wordcloud.to_image()
with BytesIO() as buffer:
    wc_img.save(buffer, 'png')
    img2 = base64.b64encode(buffer.getvalue()).decode()

topten ="SELECT count(usuario_twitteador) conteo, usuario_twitteador FROM tweets where eval_Sentimiento_resul = '-1' group by usuario_twitteador order by conteo desc;"

topTenResult = pd.read_sql(topten,connection)
connection.close()


#############################

#df = pd.read_csv('Covid19VacunasAgrupadas.csv')

#print(df)
#print(df.vacuna_nombre.nunique())
#print(df.vacuna_nombre.unique())
app = dash.Dash(__name__)

app.layout = html.Div([
    
    html.Div([
        html.H1('Análisis de Sentimientos'),
        html.Img(src='assets/escudo.png')
    ], className = 'banner'),

    html.Div([
        html.Div([
            html.P('Selecciona la palabra', className = 'fix_label', style={'color':'black', 'margin-top': '2px'}),
            dcc.RadioItems(id = 'dosis-radioitems', 
                            labelStyle = {'display': 'inline-block'},
                            options = [
                                {'label' : 'Secretaria de Hacienda de Bogotá', 'value' : 'SHD'}
                            ], value = 'SHD',
                            style = {'text-align':'center', 'color':'black'}, className = 'dcc_compon'),
        ], className = 'create_container2 five columns', style = {'margin-bottom': '20px'}),
    ], className = 'row flex-display', style = {'text-align':'center'} ),

    html.Div([
        html.Div([
            html.H6('NUBE DE PALABRAS SOBRE LA SECRETARIA DISTRITAL DE HACIENDA'),
            html.Img(src="data:assets/png;base64," + img2)
        ], className = 'create_container2 tree columns')
    ], className = 'row flex-display',style = {'text-align':'center','margin':'1%'}),

    html.Div([
        html.Div([
            html.H6('DISPERSIÓN DE SENTIMIENTOS POR FECHAS'),
            dcc.Graph(id = 'my_graph', figure = {})
        ], className = 'create_container2 eight columns'),

        html.Div([
            html.H6('PORCENTAJE DE MENSAJES POR POLARIDAD'),
            dcc.Graph(id = 'pie_graph', figure = {})
        ], className = 'create_container2 five columns')
    ], className = 'row flex-display'),
    
    html.Div([
        html.Div([
            html.H6('DISPERCIÓN DE SENTIMIENTOS NEGATIVOS POR FECHA'),
            dcc.Graph(id = 'my_graph1', figure = {})
        ], className = 'create_container2 tree columns'),
        html.Div([
            html.H6('USUARIOS CON SENTIMIENTOS NEGATIVOS EN TWEETER'),
            html.Div([
            dash_table.DataTable(
                id='table1',
                columns=[{"name": i, "id": i} for i in topTenResult.columns],
                data=topTenResult.to_dict('records'),
                filter_action = 'native',
                sort_action='native',
                page_size=10,
                style_cell={'whiteSpace':'normal','heigth':'auto','text_align':'left'},
                sort_mode = 'multi'
            )
            #dcc.Graph(id = 'my_graph2', figure = {})
            ], className = 'create_container2 tree columns',style = {'text-align':'center','margin':'1%'})
        ], className = 'create_container2 tree columns')
    ], className = 'row flex-display'),
    
    html.Div([
       html.Div([
        html.H6('VALORES POR SENTIMIENTOS NEGATIVO'),
        html.Div([
            dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in df_neg.columns],
                data=df_neg.to_dict('records'),
                filter_action = 'native',
                sort_action='native',
                page_size=10,
                style_cell={'whiteSpace':'normal','heigth':'auto','text_align':'left'},
                sort_mode = 'multi'
            )
            #dcc.Graph(id = 'my_graph2', figure = {})
        ], className = 'create_container2 tree columns',style = {'text-align':'center','margin':'1%'}),
       ], className = 'create_container2 tree columns',style = {'text-align':'center','margin':'1%'})
    ], className = 'row flex-display'),
    html.Div([
        html.H4('INTEGRANTES', style={'text-align':'center'}),
        html.P('        Carlos Augusto Cely Cely', className = 'fix_label', style={'color':'black', 'margin-top': '2px','text-align':'left'}),
        html.P('        Omar Ricardo Parra Mojica', className = 'fix_label', style={'color':'black', 'margin-top': '2px','text-align':'left'}),
        html.P('        José Rafael Ocampo Antero', className = 'fix_label', style={'color':'black', 'margin-top': '2px','text-align':'left'}),
        html.P('        Erlington Salcedo Benavides', className = 'fix_label', style={'color':'black', 'margin-top': '2px','text-align':'left'})
    ],className = 'create_container2 seven columns',style={'text-align':'center','margin':'0px auto'}),

    html.Div([
        html.H4('Secretaria Distrital de Hacienda', className = 'fix_label', style={'color':'black', 'margin-top': '2px'}),
        html.H4('Mejores Equipos de Trabajo 2021', className = 'fix_label', style={'color':'black', 'margin-top': '2px'}),
        html.H4('2021', className = 'fix_label', style={'color':'black', 'margin-top': '2px'})
    ],className = 'create_container2 five columns',style={'text-align':'center','margin':'0px auto'})

], id='mainContainer', style={'display':'flex', 'flex-direction':'column'})

@app.callback(
    Output('my_graph', component_property='figure'),
    [Input('dosis-radioitems', component_property='value')])

def update_graph(value):
    fig = px.scatter (
        data_frame = result_dF,
        x = 'Fecha_tweeter',
        y = ['Cantidad_positivos', 'Cantidad_negativos', 'Cantidad_neutros'])
    return fig

@app.callback(
    Output('pie_graph', component_property='figure'),
    [Input('dosis-radioitems', component_property='value')])

def update_graph_pie(value):
    #colors = ['read','gold','green']
    fig2 = px.pie(
        data_frame = df,
        color_discrete_sequence = ['yellow','green' ,'red'],
        names = 'Sentimiento',
        values = 'SentimientoNum')
    #fig2.update_traces(marker=dict(colors=colors))
    return fig2
@app.callback(
    Output('my_graph1', component_property='figure'),
    [Input('dosis-radioitems', component_property='value')])

def update_graph1(value):
    fig4 = px.scatter (
        data_frame = result_dF,
        x = 'Fecha_tweeter',
        y = 'Cantidad_negativos')
    return fig4

if __name__ == ('__main__'):
    app.run_server(debug=True)
