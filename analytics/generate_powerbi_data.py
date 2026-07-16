import pandas as pd
import numpy as np
import datetime
import os

def generate_powerbi_datasets():
    """Generates synthetic Fact and Dimension tables for Power BI Healthcare Dashboard."""
    print("Generating Star Schema datasets for Power BI...")
    
    out_dir = "powerbi_data"
    os.makedirs(out_dir, exist_ok=True)
    
    np.random.seed(42)
    
    # --- 1. DimDepartment ---
    departments = pd.DataFrame({
        'DepartmentID': [1, 2, 3, 4, 5],
        'DepartmentName': ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 'General Medicine'],
        'CapacityPerDay': [50, 40, 60, 80, 100]
    })
    departments.to_csv(f"{out_dir}/DimDepartment.csv", index=False)
    
    # --- 2. DimDoctor ---
    doctors = pd.DataFrame({
        'DoctorID': range(1, 16),
        'DoctorName': [f"Dr. {chr(65+i)}{chr(97+i)}smith" for i in range(15)],
        'DepartmentID': np.random.choice([1, 2, 3, 4, 5], 15)
    })
    doctors.to_csv(f"{out_dir}/DimDoctor.csv", index=False)
    
    # --- 3. DimPatient ---
    patients = pd.DataFrame({
        'PatientID': range(1, 2001),
        'PatientGender': np.random.choice(['M', 'F', 'Other'], 2000, p=[0.48, 0.50, 0.02]),
        'AgeGroup': np.random.choice(['0-18', '19-35', '36-50', '51-70', '71+'], 2000, p=[0.1, 0.25, 0.3, 0.2, 0.15])
    })
    patients.to_csv(f"{out_dir}/DimPatient.csv", index=False)
    
    # --- 4. DimDate ---
    start_date = datetime.date(2023, 1, 1)
    date_list = [start_date + datetime.timedelta(days=x) for x in range(365)]
    dim_date = pd.DataFrame({
        'DateID': [d.strftime("%Y%m%d") for d in date_list],
        'Date': date_list,
        'Year': [d.year for d in date_list],
        'Month': [d.month for d in date_list],
        'DayOfWeek': [d.strftime("%A") for d in date_list],
        'IsWeekend': [1 if d.weekday() >= 5 else 0 for d in date_list]
    })
    dim_date.to_csv(f"{out_dir}/DimDate.csv", index=False)
    
    # --- 5. FactAppointments ---
    num_appointments = 15000
    appointment_dates = np.random.choice(date_list, num_appointments)
    
    # Generate realistic status distribution
    statuses = np.random.choice(
        ['COMPLETED', 'NO_SHOW', 'CANCELLED'], 
        num_appointments, 
        p=[0.75, 0.15, 0.10]
    )
    
    fact_appointments = pd.DataFrame({
        'AppointmentID': range(1, num_appointments + 1),
        'DateID': [d.strftime("%Y%m%d") for d in appointment_dates],
        'DoctorID': np.random.choice(doctors['DoctorID'], num_appointments),
        'PatientID': np.random.choice(patients['PatientID'], num_appointments),
        'DepartmentID': np.random.choice(departments['DepartmentID'], num_appointments),
        'Status': statuses,
        'LeadTimeDays': np.random.randint(1, 30, num_appointments),
        'WaitTimeMinutes': np.random.normal(25, 10, num_appointments).clip(0, 120).astype(int),
        'IsNewPatient': np.random.choice([0, 1], num_appointments, p=[0.7, 0.3])
    })
    
    fact_appointments.to_csv(f"{out_dir}/FactAppointments.csv", index=False)
    
    print(f"Data generation complete. Saved to {os.path.abspath(out_dir)}")
    print("You can now import these CSVs directly into Power BI.")

if __name__ == "__main__":
    generate_powerbi_datasets()
