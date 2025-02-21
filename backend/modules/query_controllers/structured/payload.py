RESPONSE_REFORMAT_QUERY = """Given the user query, reformat the response to a natural language response.
Do not include any code, markdown or file paths in the response.
Also do not approximate any numberical values or facts, state them as is.
If the user asks for a chart, Just reply with: "Here is the requested chart for <query>." Do not send the image path.
Query: {query}
Response: {response}
"""

# OpenAPI examples

## CSV
CSV_STRUCTURED_QUERY = {
    "data_source_fqn": "structured::/app/user_data/loan-payments",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o",
    },
    "query": "What is the average age of people?",
}

CSV_STRUCTURED_PAYLOAD = {
    "summary": "Request payload for csv files",
    "description": "This payload is used to query csv files using PandasAI",
    "value": CSV_STRUCTURED_QUERY,
}

## GSheet
DESCRIPTION_OF_COLUMNS = """Description of columns:
1. Timestamp: Timestamp
2. Your Gender: Gender
3. Your Age in Years: Age
4. Which of these fields are you currently working in?: Department
5. What is the target market for the work you produce?: Target Market
6. Please select which of these best describes your current role: Role
7. If it applies, please list the rank of your position: Rank
8. How many years experience in your current position do you have?: Years in current role
9. How many years experience working in the visual effects industry do you have?: Total years of experience in VFX industry
10. Where are you working?: Location
11. What currency do you want to use for filling out this form?: Currency
12. What type of employment contract do you have?: Employment contract
13. How long, in months, have you been employed in your current job?: Months employed in current role
14. What payment cycle should we use to calculate your rate?: Payment cycle
15. Please specify how much you charge per payment cycle, not including overtime: Rate per payment cycle
16. How much overtime do you work, on average, per week?: Average weekly overtime hours
17. Do you get paid overtime?: Overtime pay
18. Paid OT: How many hours does your employer consider a standard working week, before overtime is calculated?: Standard working hours before overtime applies
19. Paid OT: What is your overtime rate, per hour, as a multiple of your normal pay?: Overtime rate as a multiple of normal pay
20. What percentage of your income would you attribute to Over Time pay?: The share of total income derived from overtime, expressed as a percentage.
21. Approximately how many weeks of the year do you actually charge for?: The number of weeks in a year the respondent actively works and earns income.
22. What percentage of tax would you pay on your earnings over the course of a single financial year?: Tax rate on annual earnings
23. Which of the following benefits, if any, do you receive from your employer?: Benefits provided by the employer
24. What is the total value of benefits you receive in the average financial year?: The monetary value of the benefits the respondent receives annually
25. Do you support movements to unionise the VFX workforce?: The respondent’s opinion on unionizing the visual effects workforce
26. Are you happy with the hours you are required to work in VFX?: The respondent’s satisfaction with their working hours in VFX
27. Do you like your career?: The respondent’s overall satisfaction with their career
28. Do you like the city or hub you're working in?: The respondent’s satisfaction with their current location or work hub
29. How do you feel about overtime?: The respondent’s opinion on working overtime
30. What advice would you give to people looking to get into a role like yours in the visual effects industry?: Recommendations for newcomers entering the VFX industry
31. Please estimate what you think your total income is for a financial year, before tax: Estimated annual income, including overtime but excluding benefits
32. How can we improve the survey?: Suggestions from respondents for improving the survey design or questions"""


GSHEET_STRUCTURED_QUERY = {
    "data_source_fqn": "structured::https://docs.google.com/spreadsheets/d/1hupDq5dsOVCObvEbLAJvhwoG_4l8Yec-qHSMfLx27H4/edit?usp=sharing",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o",
    },
    "query": "How many departments are there?",
    "description": DESCRIPTION_OF_COLUMNS,
}

GSHEET_STRUCTURED_PAYLOAD = {
    "summary": "Request payload for google sheets",
    "description": "This payload is used to query google sheets using PandasAI",
    "value": GSHEET_STRUCTURED_QUERY,
}

## DB
DB_STRUCTURED_QUERY = {
    "data_source_fqn": "structured::postgresql://postgres:test@cognita-db:5432/cognita-config",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o",
    },
    "query": "Give me details of all the collections",
    "table": "collections",
}

DB_STRUCTURED_PAYLOAD = {
    "summary": "Request payload for database files",
    "description": "This payload is used to query database files using PandasAI",
    "value": DB_STRUCTURED_QUERY,
}

## DB with where clause
DB_STRUCTURED_WHERE_QUERY = {
    "data_source_fqn": "structured::postgresql://postgres:test@cognita-db:5432/cognita-config",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o",
    },
    "query": "Give me count of indexing runs for collection finance-m",
    "table": "ingestion_runs",
    "where": [{"column": "collection_name", "operator": "=", "value": "finance-m"}],
}

DB_STRUCTURED_WHERE_PAYLOAD = {
    "summary": "Request payload for database files with where clause",
    "description": "This payload is used to query database files with where clause using PandasAI",
    "value": DB_STRUCTURED_WHERE_QUERY,
}

## CSV with plotting
CSV_STRUCTURED_PLOTTING_QUERY = {
    "data_source_fqn": "structured::/app/user_data/employee",
    "model_configuration": {
        "name": "truefoundry/openai-main/gpt-4o",
    },
    "query": "Plot a pie chart of the percentage of employees in each department",
}

CSV_STRUCTURED_PLOTTING_PAYLOAD = {
    "summary": "Request payload for csv files with plotting",
    "description": "This payload is used to query csv files with plotting using PandasAI",
    "value": CSV_STRUCTURED_PLOTTING_QUERY,
}
