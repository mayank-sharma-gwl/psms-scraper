import requests
import pandas as pd

def fetch_station_ids(username, headers):
    url = f'https://bits-psms-api-prod.azurewebsites.net/api/StationAllotment/stationFinalPreferenceByStudent/{username}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        station_data = response.json()
        station_ids = [station['stationId'] for station in station_data]
        return station_ids
    return []

def fetch_net_reqs(station_id, headers):
    url = f"https://bits-psms-api-prod.azurewebsites.net/api/ProblemBank/listview/?stationId={station_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        problem_bank_data = response.json().get('problemBankGridLines', [])
        if problem_bank_data:
            return problem_bank_data[0]['totalRequirement']
    return None

def fetch_problem_bank_id(userName, station_id, headers):
    url = f"https://bits-psms-api-prod.azurewebsites.net/api/stationallotment/student/preference/problembanks?stationId={station_id}&userName={userName}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        problem_bank_data = response.json().get('problemBankGridLines', [])
        if problem_bank_data:
            return problem_bank_data[0]['problemBankId'], problem_bank_data[0]['stationName'], problem_bank_data[0]['stationCity'], problem_bank_data[0]['totalRequirement'], problem_bank_data[0]['stationId']
    return None, None, None, None, None

def fetch_projects(userName, problem_bank_id, headers):
    url = f"https://bits-psms-api-prod.azurewebsites.net/api/stationallotment/student/preference/projects?problemBankId={problem_bank_id}&userName={userName}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('projectGridLines', [])
    return []

def fetch_project_details(project_id, headers):
    url = f"https://bits-psms-api-prod.azurewebsites.net/api/ProblemBank/project/{project_id}?expand=all"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        project_data = response.json()
        project_discipline = project_data.get('projectDiscipline', [])
        project_facility = project_data.get('projectFacility', [])
        if project_discipline and project_facility:
            totalReq = project_discipline[0].get('totalRequirement', 'N/A')
            min_cgpa = project_discipline[0].get('cgpamin', 'N/A')
            max_cgpa = project_discipline[0].get('cgpamax', 'N/A')
            ug_stipend = project_facility[0].get('ugstipend', 'N/A')
            branch_eligibility = project_discipline[0].get('disciplineCodes', 'N/A')
            return totalReq, min_cgpa, max_cgpa, ug_stipend, branch_eligibility
    return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

def main():
    print("Script Started")
    json_data = {
        'userId': 0,
        'userName': 'Enter your bits email ID',
        'name': '',
        'roleId': 0,
        'roleName': '',
        'password': 'Enter your PSMS password',
    }

    userName = json_data.get('userName')

    login_url = 'https://bits-psms-api-prod.azurewebsites.net/api/Users/login'

    with requests.Session() as s:
        login_response = s.post(login_url, json=json_data)
        
        if login_response.status_code == 200:
            print("Login successful!")
            login_data = login_response.json()
            token = login_data.get('token')
            
            if not token:
                print("Token not found in the login response")
                exit()

            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }

            print("Scraping started")
            print("Do not exit, scraping takes around 10-15 minutes depending on your internet speed")

            station_ids = fetch_station_ids(userName, headers)
            output_data = []
            failed_ids = []

            for station_id in station_ids:
                problem_bank_id, station_name, station_city, total_req, stationId = fetch_problem_bank_id(userName, station_id, headers)
                total_new_req = fetch_net_reqs(station_id, headers=headers)

                if not problem_bank_id:
                    failed_ids.append(station_id)
                    
                if problem_bank_id:
                    projects = fetch_projects(userName, problem_bank_id, headers)
                    for project in projects:
                        project_id = project['projectId']
                        totalReq, min_cgpa, max_cgpa, ug_stipend, branch_eligibility = fetch_project_details(project_id, headers)
                        output_data.append([
                            station_name, station_city, total_new_req ,totalReq, ug_stipend, branch_eligibility, project['title'], project['description'],  min_cgpa, max_cgpa
                        ])
            
            output_df = pd.DataFrame(output_data, columns=['Station Name', 'Station City', 'Total Company Req', 'Total Req', 'Stipend', 'Branch Eligibility', 'Project Title', 'Project Description', 'Min CGPA', 'Max CGPA'])
            output_file_path = 'output_projects.xlsx'
            output_df.to_excel(output_file_path, index=False)
            
            print(f"Data saved to {output_file_path}")
            print("Failed to fetch data for station id's: ", failed_ids)

        else:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")

if __name__ == "__main__":
    main()
