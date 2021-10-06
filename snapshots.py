#!/usr/bin/python3

import boto3
import logging
import argparse
import sys

from datetime import date
from datetime import timedelta

def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : %(levelname)s : %(funcName)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="AWS Auditor")
    parser.add_argument(
        "--profile",
        help="aws profile",
        dest="p",
        required=False,
        metavar="<profile>"
    )
    args = parser.parse_args()

    if args.p:
        try:
            session = boto3.session.Session(profile_name=args.p)
        except boto3.exceptions.botocore.exceptions.ProfileNotFound:
            logging.error("profile not found! try harder...")
            sys.exit(0)
    else:        
        session = boto3.session.Session()
        if session.get_credentials() == None:
            logging.error("you have not configured any default credentials in ~/.aws/credentials")
            sys.exit(0)

    try:
        logging.info("using {}".format(session.client('sts').get_caller_identity()["Arn"]))
    except boto3.exceptions.botocore.exceptions.ClientError:
        logging.error("invalid credentals!")
        sys.exit(0)
    
    logging.info("getting ebs snapshots")
    client = session.client('ec2', region_name="eu-west-2")
    for region in client.describe_regions()["Regions"]:
        client = session.client('ec2', region_name=region["RegionName"])
        for snapshot in client.describe_snapshots(OwnerIds=["self"])["Snapshots"]:
            year, month, day = str(snapshot["StartTime"]).split(" ")[0].split("-") #convert datetime to string so it can be converted to date and compare with time delta
            start_date = date(int(year), int(month), int(day)) # extract date, ignore time
            if start_date < (date.today() - timedelta(days=365)):
                print(snapshot["SnapshotId"])
                try:
                    client.delete_snapshot(SnapshotId=snapshot["SnapshotId"])# DryRun=True|False )
                except boto3.exceptions.botocore.exceptions.ClientError:
                    logging.warning("could not delete {}:{} likely in use".format(snapshot["SnapshotId"], region["RegionName"]))

                



        
        



if __name__ == "__main__":
    main()