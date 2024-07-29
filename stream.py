import os
import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI

load_dotenv('./.env')

def parse_appointment():
    df_appointment = pd.read_csv("appointments.csv")
    df_appointment['Date'] = pd.to_datetime(df_appointment['Date']).dt.date
    df_appointment['Start'] = pd.to_datetime(df_appointment['Start'],format= '%H:%M:%S' ).dt.time
    df_appointment['End'] = pd.to_datetime(df_appointment['End'],format= '%H:%M:%S' ).dt.time

    return df_appointment

def get_availability(df_appointment):
    open_hour = datetime.datetime.strptime('08:00:00', '%H:%M:%S').time()
    last_appointment_hour = datetime.datetime.strptime('16:00:00', '%H:%M:%S').time()
    idx = pd.date_range("2024-07-26", '2024-12-31', freq="h")
    ts = pd.Series(range(len(idx)), index=idx)
    df_timeslot = pd.DataFrame({'date':ts.index.date,'timeslot':ts.index.time})
    df_timeslot = df_timeslot[df_timeslot['timeslot'].between(open_hour,last_appointment_hour)]
    
    df_merge = pd.merge(df_timeslot, df_appointment, how="left", left_on=['date'], right_on=['Date']) 
    df_occupied = df_merge[((df_merge['timeslot'] >= df_merge['Start']) & (df_merge['timeslot'] < df_merge['End']))][['date','timeslot']]
    df_availability = pd.merge(df_timeslot, df_occupied, how='outer', on=['date', 'timeslot'], indicator=True)
    df_availability = df_availability[(df_availability['_merge'] == 'left_only')][['date', 'timeslot']]
    df_availability['date'] = df_availability['date'].astype(str)
    df_availability['timeslot'] = df_availability['timeslot'].astype(str)
    df_availability['free'] = 1

    df_availability.to_csv('availability.csv', index=False)

    return df_availability

def agent_executor(availability):
    llm = ChatOpenAI(temperature=0.6)
    agent_executor = create_csv_agent(
        llm,
        'availability.csv',
        agent_type="tool-calling",
        verbose=True,
        stream=True,
        allow_dangerous_code=True
    )
    return agent_executor

def update_appointment(name, df_appointment):
    df = pd.read_csv("availability.csv")
    df = df[df['free'] == 0][['date', 'timeslot']]
    df['Name'] = name
    df['Date'] = df['date']
    df['Start'] = df['timeslot']
    df['End'] = df['timeslot']
    df = df.drop(['date', 'timeslot'], axis=1) 

    print(df.head())
    df = pd.concat([df, df_appointment], ignore_index=True, sort=False)
    df.to_csv('appointments.csv', index=False)

if __name__ == "__main__":

    st.set_page_config(page_title='Chatbot Appointments')
    st.header('Ask Available Schedule')

    appointment = parse_appointment()
    availability = get_availability(appointment)

    user_name = st.text_input("My name: ")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    if prompt := st.chat_input('ask me anything'):
        with st.chat_message('user'):
            st.markdown(prompt)
        st.session_state.messages.append({'role':user_name,'content':prompt})

        with st.chat_message('assistant'):
            executor = agent_executor(availability)
            if prompt in ("bye", "thank you"):
                response = 'Happy to help'
            else:
                response = executor.invoke(prompt)
                executor.invoke('export the updated dataframe to availability.csv')
                update_appointment(user_name, appointment)
            st.markdown(response['output'])
            st.session_state.messages.append({'role':'assistant','content':response['output']})