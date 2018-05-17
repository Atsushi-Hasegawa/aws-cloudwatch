#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import boto3
import json

class CloudWatch:

    def __init__(self, file):
        self.config = self.load_config(file)

    def initialize(self):
        self.ec2 = boto3.client('ec2', region_name=self.config["region_name"])
        self.instances = self.load_all_instances()
        self.cloudwatch = boto3.client('cloudwatch', region_name=self.config["region_name"])
      
    def get_client(self):
        return self.ec2

    def get_cloudwatch_client(self):
        return self.cloudwatch

    def load_config(self, file):
        file_path=os.path.abspath(file)
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print "[Error]: Not Found Directory or File"
            return []
   
    def load_all_instances(self):
        response = self.ec2.describe_instances()
        return [ instance for res in response.get('Reservations', []) for instance in res.get('Instances', [])]

    def load_instance(self, state=None):
        if not state: return self.instances

        record = []
        for res in self.instances:
            if state == res['State']['Name']:
                record.append(res)

        return record

    def put_alarm_metric(self, instance, tag, config):
        if not instance or not self.config: return []

        record = [{
            "Name": "InstanceId",
            "Value": instance["InstanceId"]
        }]
        if config["dimensions"]:
            for alarm in config["dimensions"]:
                record.append({
                    "Name": alarm["Name"],
                    "Value": alarm["Value"]
                })
        return self.cloudwatch.put_metric_alarm(
                AlarmName=tag["Value"] + config["alarm_name"],
                AlarmDescription=tag["Value"] + config["alarm_description"],
                ActionsEnabled=True,
                OKActions=[],
                AlarmActions=[config['alarm_actions']],
                InsufficientDataActions=[],
                MetricName=config["metric_name"],
                Namespace=config["namespace"],
                Statistic=config["statistic"],
                Dimensions=record,
                Period=int(config["period"]),
                Unit=config["unit"],
                EvaluationPeriods=1,
                DatapointsToAlarm=1,
                Threshold=int(config["threshold"]),
                ComparisonOperator=config["comparision_operator"],
                TreatMissingData=config["treat_missing_data"]
                )

    def load_alarm_for_metric(self, instance, namespace, metricname):
        if not instance or namespace or metricname: return []

        return self.cloudwatch.describe_alarms_for_metric(
                MetricName=metricname,
                Namespace=namespace,
                Dimensions=[
                    {
                        "Name": "InstanceId",
                        "Value": instance
                    }
                ]
        )

    def main(self):
        if not self.config: return []

        self.initialize()
        instances = self.load_instance()
        tag_name=""
        for instance in instances:
            for tag in instance["Tags"]:
                if tag["Key"] == "NickName" and tag["Value"].find(tag_name) != -1:
                    for config in self.config['alarm_metrics']:
                        self.put_alarm_metric(instance, tag, config)

if __name__ == "__main__":
    file="cloudwatch.json"
    cloudwatch = CloudWatch(file)
    cloudwatch.main()
