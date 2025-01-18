# EC2 Instance Manager

A web application for managing AWS EC2 instances.
After the completion of this setup, you will have a web application for stoping, starting and checking the status of AWS EC2 instances.

One of the benefit of this web application is the ability to stop the EC2 instances when they are not in use. This will help you save money on AWS. Therefore, if you have an EC2 instance that does not require 100% availability, you can stop it when it is not in use and start it when you need it directly from the web application.

The web application is itself hosted on a EC2 instance using a lite and low cost Ubuntu Linux image. A Terraform script is used to create the infrastructure and the application is deployed on the instance.

Please ensure you have the AWS access keys for the account that is used to create the target EC2 instance.


## Project Structure

``` text
├── ec2-instance-manager-app
│   ├── app.py
│   ├── aws_cli_utils.py
│   ├── requirements.txt
│   └── templates
│       └── index.html
├── ec2-instance-manager-server
│    ├── .terraform.lock.hcl
|    └── main.tf
├── LICENSE
├── README.md
└── .gitignore
```

## Prerequisites

- AWS Account (Free Tier eligible)
- Terraform installed on your local machine (v1.0.0+)
- Python 3.10+

## Server Deployment (ec2-instance-manager-server)
The first step is to prepare the server that will host the web application.

### Initial Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/ife0042/ec2-instance-manager.git
   ```

2. Set AWS Access Keys:
To obtain the AWS access keys (Access Key ID & Secret Access Key) from the AWS IAM console, please refer to the AWS IAM documentation. These keys are required by the Terraform script to create an EC2 instance.
After obtaining the access keys, set them in the environment variables of your local machine by following the instructions below:
   ```bash
   export AWS_ACCESS_KEY_ID=xxxxxxxxx
   export AWS_SECRET_ACCESS_KEY=xxxxxxxxx
   ```

### Deploy Infrastructure
Once the AWS access keys are set, you can deploy the infrastructure using terraform by running the following commands:
1. Change directory to the ec2-instance-manager-server directory:
   ```bash
   cd ec2-instance-manager-server
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Review the infrastructure plan:
   ```bash
   terraform plan
   ```

4. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

After successful deployment, you'll find two new files in the `ec2-instance-manager-server` directory:
- `public_ip.txt` containing your EC2 instance's public IP. This IP will later be used to access the application over the internet.
- `ec2-instance-manager-key.pem` for SSH access to the instance

## Connect to the EC2 instance
Once the infrastructure is deployed, you can connect to the EC2 instance using the following command (ensure you are in the `ec2-instance-manager-server` directory):
   ```bash
   ssh -i ec2-instance-manager-key.pem ubuntu@$(cat public_ip.txt)
   ```

## Application Deployment (ec2-instance-manager-app)
Now that you have connected to the EC2 instance, you can deploy the application.
Please note that the application will be assigned to the port 4999. This is to avoid conflicts with other application that might be using the default Flask port 5000.

1. The first step is to clone the repository in the host machine.
   ```bash
   git clone https://github.com/ife0042/ec2-instance-manager.git
   ```

2. Install and upgrade system packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. Reboot the system to ensure the system is up to date. Refer to the "Connect to the EC2 instance" section on how to connect back to the EC2 instance.
   ```bash
   sudo reboot
   ```

4. Install Python, pip, venv and nginx:
Nginx is used to serve the application and venv is used to create a virtual environment for the application.
   ```bash
   sudo apt install python3.10 python3-pip python3.10-venv nginx -y
   ```

5. Set the AWS secret keys as environment variables in the host machine:
   ```bash
   export AWS_ACCESS_KEY_ID=xxxxxxxxx
   export AWS_SECRET_ACCESS_KEY=xxxxxxxxx
   ```

6. Create a new Nginx configuration file:
   ```bash
   sudo vim /etc/nginx/sites-available/ec2-instance-manager
   ```

7. Add the following content to the file:
In the file, replace the `your_domain.com` with the public IP of the EC2 instance.
   ```
   server {
      listen 80;
      server_name your_domain.com;  # Replace with your domain or server IP

      location / {
         proxy_pass http://127.0.0.1:4999;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header X-Forwarded-Proto $scheme;
      }
   }
   ```

8. Enable the site and restart Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/ec2-instance-manager /etc/nginx/sites-enabled
   sudo nginx -t  # Test the configuration
   sudo systemctl restart nginx
   ```

9. Create Python virtual environment:
Set your current directory to the ec2-instance-manager-app directory and create a virtual environment:
   ```bash
   cd ec2-instance-manager/ec2-instance-manager-app
   python3.10 -m venv .env
   source .env/bin/activate
   ```

10. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

11. Run the application using Gunicorn:
   ```bash
   gunicorn -w 4 --bind 0.0.0.0:4999 --access-logfile - --error-logfile - app:app
   ```
https://flask.palletsprojects.com/en/stable/deploying/gunicorn/


### Access the application
The web application should now be available at `http://<public-ip>`.
To control another EC2 instance, Expand the "Add New Configuration" section and enter the instance_id of the target EC2 machine and click on the "Start" or "Stop" button. Watch the log and the status bar change to reflect the current status of the target EC2 instance.

Alternatively, if the instance_id is saved in an S3 object, you can provide the bucket name and the object key and the content will be automatically fetched - this assumes the S3 bucket is in the same AWS account as the EC2 instance.


### Using CLI

You can also use the CLI to start, stop and check the status of the EC2 instances. Run the following command to execute actions against your target EC2 instance:

```bash
python3.10 aws_cli_utils.py <action> <instance-id>
```
Where `<action>` is one of the following: `start`, `stop`, `status`.

Ensure you are in the `ec2-instance-manager-app` directory and have the AWS credentials set in your environment variables.


## License

This project is licensed under the GNU General Public License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.
