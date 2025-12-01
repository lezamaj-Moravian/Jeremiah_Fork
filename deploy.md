# Deployment Guide

## Local Development

To deploy and run the application locally, follow these steps:

### Prerequisites
- Python 3.7 or higher installed on your system

### Setup Instructions

1. **Navigate to the project directory:**
   ```bash
   cd Amanda-Jeremaiah-William-Tori
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment:**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```
   
   Or alternatively:
   ```bash
   flask run
   ```

6. **Access the application:**
   - Open your browser and navigate to: `http://localhost:5000` or `http://127.0.0.1:5000`



## Deploy on AWS

1. Create your EC2 instance on AWS
Paste this into your User Data when creating the instance:
```bash
yum install -y git
git clone https://github.com/cs298f25/Amanda-Jeremaiah-William-Tori.git
cd /Amanda-Jeremaiah-William-Tori
chmod +x ec2-deploy.sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp stravaapp.service /etc/systemd/system
systemctl enable stravaapp.service
systemctl start stravaapp.service
```
        
3. SSH into your created instance
```bash
ssh -i ~/.ssh/labsuser.pem ec2-user@<IPv 4 address>
```
   
3. Install Git
```bash
sudo yum install -y git
```
        
4. Clone the repo into your EC2 instance
```bash
git clone https://github.com/cs298f25/Amanda-Jeremaiah-William-Tori.git
cd Amanda-Jeremaiah-William-Tori
```

5. Change permissions on the script file
```bash
chmod +x userdata.sh
```     

6. Run the Deploy script
```bash
sudo ./userdata.sh
```

7. Access the Web Page
```bash
http://[your-public-ip]:8000
```





### Note
- The app runs in development mode by default
- To stop the server, press `Ctrl+C` in your terminal
