# appointment_chatbot_with_csv

PRE-REQUISITE:
- python
- install pipenv `pip install pipenv`
  Required packages have been included within the pipenv (re: `Pipfile`)

To execute:
1. change `.env.dist` to `.env`.
2. Set the `OPEN_API_KEY` variable.
3. Run `pipenv install` will create a virtual env along with the necessary packages.
4. Chatbot through terminal : Run `pipenv run python main.py`.
5. Chatbot through a web : Run `pipenv run  streamlit run python stream.py` and the browser should be opened to `http://localhost:8501/`.
6. to stop:
   streamlit : CTRL+C
   terminal : Input 'Bye'