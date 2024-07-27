import os
import datetime
import pandas as pd
from dotenv import load_dotenv
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
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
    idx = pd.date_range("2024-07-01", '2024-12-31', freq="h")
    ts = pd.Series(range(len(idx)), index=idx)
    df_timeslot = pd.DataFrame({'date':ts.index.date,'timeslot':ts.index.time})
    df_timeslot = df_timeslot[df_timeslot['timeslot'].between(open_hour,last_appointment_hour)]
    
    df_merge = pd.merge(df_timeslot, df_appointment, how="left", left_on=['date'], right_on=['Date']) 
    df_occupied = df_merge[((df_merge['timeslot'] >= df_merge['Start']) & (df_merge['timeslot'] < df_merge['End']))][['date','timeslot']]
    df_availability = pd.merge(df_timeslot, df_occupied, how='outer', on=['date', 'timeslot'], indicator=True)
    df_availability = df_availability[(df_availability['_merge'] == 'left_only')][['date', 'timeslot']]
    df_availability['appointment_date'] = df_availability['date'].astype(str)
    df_availability['available_timeslot'] = df_availability['timeslot'].astype(str)
    df_availability['booked'] = 0
    df_availability = df_availability.drop(['date', 'timeslot'], axis=1) 

    return df_availability

def update_appointment(name, df_appointment):
    df = pd.read_csv("data.csv")
    df = df[df['booked'] == 1][['appointment_date', 'available_timeslot']]
    df['Name'] = name
    df['Date'] = df['appointment_date']
    df['Start'] = df['available_timeslot']
    df['End'] = df['available_timeslot']
    df = df.drop(['appointment_date', 'available_timeslot'], axis=1) 
    df = pd.concat([df, df_appointment], ignore_index=True, sort=False)
    df.to_csv('appointments.csv', index=False)
    os.remove("data.csv")

    print(df.head())

if __name__ == "__main__":

    appointment = parse_appointment()
    availability = get_availability(appointment)
    
    llm = ChatOpenAI(temperature=0.3)
    agent_executor = create_pandas_dataframe_agent(
        llm,
        availability,
        agent_type="tool-calling",
        verbose=True,
        allow_dangerous_code=True
    )
    
    print("hello, what's you name")
    name_input= input("I am: ")
    print("Nice to meet you "+name_input+" how can I help?")
    
    while True:
        user_input= input("You: ")
        if user_input.lower() in ("bye"):
            agent_executor.run("export dataframe to data.csv and replace the existing file")
            update_appointment(name_input,appointment)
            break
        response = agent_executor.run(user_input)
        print("chatbot: "+response)
    