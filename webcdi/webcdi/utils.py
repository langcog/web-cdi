import os
import urllib.request


def is_ec2_linux():
    """Detect if we are running on an EC2 Linux Instance
       See http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/identify_ec2_instances.html
    """
    if os.path.isfile("/sys/hypervisor/uuid"):
        with open("/sys/hypervisor/uuid") as f:
            uuid = f.read()
            return uuid.startswith("ec2")
    return False


def get_linux_ec2_private_ip():
    """Get the private IP Address of the machine if running on an EC2 linux server"""
    if not is_ec2_linux():
        return None
    try:
        response = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/local-ipv4')
        return response.read()
    except:
        return None
    finally:
        if response:
            response.close()
