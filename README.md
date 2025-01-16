# EC2 Instance Manager

A web application for managing AWS EC2 instances with a Terraform-managed infrastructure.
After the completion of this setup, you will be able to access a web application for stoping, starting and checking the status of your EC2 instance.

One of the benefit of this web application is the ability to stop the EC2 instance when it is not in use. This will help you save money on AWS. Therefore, if you have and EC2 instance that does not require 100% availability, you can stop it when it is not in use.

Please note that this web application will be hosted on an EC2 instance using AWS Free Tier as defined in the Terraform configuration.

## Project Structure

├── ec2-instance-manager-app/        # Flask application
│   ├── app/                        # Application source code
│   ├── Dockerfile                  # Container configuration
│   ├── aws_credentials.sh          # AWS credentials setup script
│   └── requirements.txt            # Python dependencies
└── ec2-instance-manager-server/    # Terraform infrastructure
    ├── main.tf                     # Main Terraform configuration
    ├── variables.tf                # Terraform variables
    └── outputs.tf                  # Terraform outputs


## Prerequisites

- AWS Account (Free Tier eligible)
- Terraform installed (v1.0.0+)
- Docker installed (for running the application) [optional]
- Python 3.8+

## Server Deployment (ec2-instance-manager-server)
The first step is to prepare the server that will host the web application.

### Initial Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ec2-instance-manager.git
   cd ec2-instance-manager-server
   ```

2. Set AWS Access Keys:
To obtain the AWS access keys from the AWS IAM console, please refer to the AWS IAM documentation.
After obtaining the access keys, set them in the environment variables of your local machine by following the instructions below:
   ```bash
   export AWS_ACCESS_KEY_ID=xxxxxxxxx
   export AWS_SECRET_ACCESS_KEY=xxxxxxxxx
   ```

### Deploy Infrastructure
Once the AWS access keys are set, you can deploy the infrastructure using terraform by running the following commands:
1. Initialize Terraform:
   ```bash
   terraform init
   ```

2. Review the infrastructure plan:
   ```bash
   terraform plan
   ```

3. Deploy the infrastructure:
   ```bash
   terraform apply
   ```

After successful deployment, you'll find two new files in the `ec2-instance-manager-server` directory:
- `public_ip.txt` containing your EC2 instance's public IP
- `ec2-instance-manager-key.pem` for SSH access to the instance

## Connect to the EC2 instance

Once the infrastructure is deployed, you can connect to the EC2 instance using the following command:
```bash
ssh -i ec2-instance-manager-key.pem ubuntu@$(cat public_ip.txt)
```

## Application Deployment (ec2-instance-manager-app)
Now that you have connected to the EC2 instance, you can deploy the application.
Please note that the application is assigned to the port 4999. This is to avoid conflicts with other application that might be using the default Flask port 5000.
The first step is to clone the repository in host machine and install the dependencies.

```bash
git clone https://github.com/ife0042/ec2-instance-manager.git
cd ec2-instance-manager/ec2-instance-manager-app
```

Install and upgrade system packages:
```bash
sudo apt update && sudo apt upgrade -y
```

There are two ways to deploy the application:
1. In a Docker container
2. Directly in the host machine

### In a Docker container

1. Install Docker in the host machine:
   ```bash
   sudo apt install docker.io -y
   ```

2. Build and run the Docker container:
   ```bash
   cd ../ec2-instance-manager-app
   docker build -t ec2-instance-manager-app .
   docker run -d -p 4999:4999 ec2-instance-manager-app env AWS_ACCESS_KEY_ID=xxxxxxxxx AWS_SECRET_ACCESS_KEY=xxxxxxxxx
   ```

2. Access the application at `http://localhost:4999`

3. Make the application available over the internet:



### Directly in the host machine

1. Install and upgrade system packages:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. Install Python 3.8:
   ```bash
   sudo apt install python3.10 python3-pip -y
   ```

3. Install the dependencies:
   ```bash
   cd ../ec2-instance-manager-app/app
   pip3 install -r requirements.txt
   ```

4. UFW (Ubuntu Firewall): Allow traffic on port 4999:
   ```bash
   sudo ufw allow 4999
   ```

5. Run the application using Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:4999 app:app
   ```
   https://flask.palletsprojects.com/en/stable/deploying/gunicorn/


### Access the application
The web application should now be available at `http://<public-ip>`.
To control another EC2 instance, enter the instance_id of the target EC2 machine and click on the "Start" or "Stop" button. Watch the log and the status bar change to reflect the curretn status of the target EC2 instance.


## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.
