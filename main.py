import pandas as pd
import streamlit as st
import requests
from datetime import datetime
import matplotlib.pyplot as plt

def dat_transform(df):
    df['rolling_mean'] =df.groupby(by='city')['temperature'].transform(lambda x: x.rolling(window=30, min_periods=1).mean())
    df['mean'] = df.groupby(by=['city', 'season'])['temperature'].transform(lambda x: x.mean())
    df['std'] = df.groupby(by=['city', 'season'])['temperature'].transform(lambda x: x.std())
    df['anomaly'] = (df['temperature'] < df['mean'] - df['std'] * 2) + (df['temperature'] > df['mean'] + df['std'] * 2)
    return df

def get_temp(city, key):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric'
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        return data['main']['temp']
    else:
        return None
                
def is_normal(df, season, city):
    temp = get_temp(city, API_KEY)
    std = df[(df['city'] == city) & (df['season'] == season)]['std'].iloc[0]
    mean = df[(df['city'] == city) & (df['season'] == season)]['mean'].iloc[0]
    low = mean - 2 * std
    height = mean + 2 * std
    if low < temp < height:
        return f'Температура {temp} является нормой для города {city}'
    return f'Температура {temp} является аномалией для города {city}'

winter = [12, 1, 2]
spring = [3, 4, 5]
summer = [6, 7, 8]
autumn = [9, 10, 11]

def season_dec(month):
    if month in winter:
        return "winter"
    elif month in spring:
        return "spring"
    elif month in summer:
        return "summer"
    else:
        return "autumn"
    
st.header('Анализ тепературы')
uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.write("Данные успешно загружены!")
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    st.dataframe(data)

    st.header("Статистика по выбранному городу")
    city = st.selectbox("Выберите город", data['city'].unique())
    st.write(f"Выбранный город: {city!r}")

    data = dat_transform(data)

    city_describe = data[data['city'] == city]
    if st.checkbox("Показать описательную статистику"):
        st.write(city_describe.describe())

    if st.checkbox("Показать временной ряд температур для выбранного города"):
        plt.subplots() 
        fig = plt.figure()
        anomal = data[(data['anomaly'] == True) & (data['city'] == city)]
        normal = data[(data['anomaly'] == False) & (data['city'] == city)]
        plt.plot(normal['timestamp'], normal['temperature'], label='Норма', color='green')
        plt.scatter(anomal['timestamp'], anomal['temperature'], color='red', label='Аномалия')
        plt.title('Временной ряд температур с выделением аномалий')
        plt.xlabel('Дата')
        plt.ylabel('Температура')
        plt.grid(True)
        st.pyplot(fig)

    if st.checkbox("Показать сезонные профили"):
        season_data = data.groupby('season')['temperature'].agg(mean='mean', std='std').reset_index()
        plt.subplots()
        fig = plt.figure()
        season = season_data['season'].unique()
        mean = season_data['mean'].unique()
        std = season_data['std'].unique()
        plt.errorbar(x=season, y=mean, yerr=std, fmt='o-',  color='green', ecolor='black', elinewidth=2, markerfacecolor='red') 
        plt.title('Сезонные профили с указанием среднего и стандартного отклонения') 
        plt.xlabel('Сезон') 
        plt.ylabel('Среднее значение') 
        plt.grid(axis='y') 
        st.pyplot(fig)



    st.header("Введите API ключ")
    API_KEY = st.text_input("API key")

    if API_KEY:
        if get_temp(city, API_KEY) is None:
            st.error({"cod":401, "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."})
        else:
            month = datetime.now().month
            season = season_dec(month)
            st.success(is_normal(data, season, city))
                
else:
    st.write("Пожалуйста, загрузите CSV-файл.")



