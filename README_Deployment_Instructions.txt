Pakistan LPG Survey Dashboard - Streamlit Deployment Package
===========================================================

Package contents
----------------
1. streamlit_app.py
   Main app file for Streamlit Cloud deployment.

2. DashLPG_Research_Improved_Final_FORMATTED.py
   Same dashboard file retained with the working project filename.

3. Clean-Data-lpg-survey.csv
   Cleaned survey dataset. Keep this file in the same folder as streamlit_app.py.

4. requirements.txt
   Python libraries required by Streamlit Cloud.

5. .streamlit/config.toml
   Dashboard theme and server configuration.

Local run command
-----------------
Open PowerShell and run:

cd "C:\Ahmed Zahid Malik\Python\LPG Survey Dashboard"
python -m streamlit run streamlit_app.py

If you want to run the original named file:

python -m streamlit run DashLPG_Research_Improved_Final_FORMATTED.py

Streamlit Cloud deployment steps
--------------------------------
1. Create a new GitHub repository.
2. Upload all files from this package into the repository root folder.
3. Go to https://share.streamlit.io or Streamlit Community Cloud.
4. Select the GitHub repository.
5. Set the main file path as:

streamlit_app.py

6. Deploy the app.

Important notes
---------------
- Do not rename Clean-Data-lpg-survey.csv unless you also update the Python file.
- The dashboard already searches for the CSV beside the app file, which is suitable for Streamlit Cloud.
- The dashboard uses percentage-first analysis for income, area, and sector comparisons to avoid skew from unequal respondent counts.
- Income analysis is based on G8 Income Band and should be interpreted mainly for household / residential respondents.
- Keep any personal identifiers out of the public deployment if sharing externally.

Recommended external-sharing caution
------------------------------------
Before sharing with external parties, review the CSV and remove personal identifiers such as names, phone numbers, exact addresses, emails, CNIC numbers, or license details if any are present.
