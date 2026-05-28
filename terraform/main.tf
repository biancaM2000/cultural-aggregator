#Specific provider AWS
terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
}
provider "aws" {
  region     = "eu-central-1" # Regiunea Frankfurt
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

#variabile pentru credentiale
variable "aws_access_key" { type = string }
variable "aws_secret_key" { type = string }

#creez Security Group/Firewall
resource "aws_security_group" "agregator_sg" {
  name        = "agregator-events-sg"
  description = "Permite traficul SSH si HTTP pentru aplicatie"

  # Portul 22 pentru conexiunea SSH (Ansible se va lega aici)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Portul 5000 pentru aplicatia noastra Flask
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Permitem serverului sa comunice cu exteriorul (pentru update-uri si descarcat Docker)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_key_pair" "proiect_key" {
  key_name   = "cheie-proiect-devops"
  public_key = file("~/.ssh/id_rsa_proiect.pub")
}

# 3. Creez instanta EC2 (serverul Linux Ubuntu)
resource "aws_instance" "agregator_server" {
  ami           = "ami-0084a47cc718c111a" 
  instance_type = "t3.micro"
  key_name      = aws_key_pair.proiect_key.key_name # <-- ADAUGĂ ACEASTĂ LINIE

  vpc_security_group_ids = [aws_security_group.agregator_sg.id]

  tags = {
    Name = "Server-Agregator-Cultural"
  }
}

# 4.Afisez IP-ul public al serverului dupa ce e credentiale
output "server_public_ip" {
  value       = aws_instance.agregator_server.public_ip
  description = "IP-ul public al serverului creat. Vom pune acest IP in Ansible."
}