resource "aws_instance" "example" {
    ami           = "ami-0dacb0c129b49f529"
    instance_type = "t2.micro"
    key_name="linux2"

    tags = {
        Name = "bl16266_cnd2"
    }
    
    security_groups = [
        "bl16266_cnd2"
    ]
}