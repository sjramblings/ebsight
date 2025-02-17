# EBSight: Intelligent EBS Volume Analyzer

![EBSight](./ebsight.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Introduction

EBSight is a Python-based analysis tool developed in response to AWS's [new EBS snapshot size reporting feature](https://aws.amazon.com/about-aws/whats-new/2025/02/amazon-ebs-full-snapshot-size-information-console-api/). This tool leverages the newly introduced `FullSnapshotSizeInBytes` field to provide comprehensive insights into EBS volume usage, performance metrics, and cost optimization opportunities.

### Understanding EBS Snapshots

EBS snapshots are incremental in nature, meaning:

- Each snapshot only stores new or modified blocks
- Unchanged blocks are referenced from previous snapshots
- The full snapshot size represents the total data footprint at the time of the snapshot

For example:

- If you have a 100 GB volume with 50 GB of data
- The 'full snapshot size' will show 50 GB
- This remains true whether it's the first snapshot or a subsequent one
- EBSight uses this information to accurately track data changes over time

### How EBSight Helps

EBSight utilizes AWS's new snapshot size reporting to:

1. Track actual data usage versus allocated volume size
2. Monitor data change patterns over time
3. Calculate storage efficiency metrics
4. Provide cost optimization recommendations

## Key Features

### Volume Analysis

- Tracks total snapshot sizes
- Calculates daily change rates
- Monitors volume usage percentages
- Provides detailed IOPS and throughput metrics

### Performance Metrics

- P99 and Peak IOPS for read/write operations
- Throughput measurements in MBps
- Queue length monitoring
- Historical performance data over 7-day periods

### Visualization Options

- ASCII-based bar graphs for size comparisons
- Consolidated summary tables
- Optional CSV export functionality
- FSx for NetApp ONTAP sizing recommendations

## Usage

### Basic Command

```bash
python ebsight.py
```

### Available Options

```bash
python ebsight.py [OPTIONS]
Options:
--verbose, -v Show detailed snapshot information
--csv, -c Export results to CSV
--graph, -g Show ASCII graphs
--profile, -p AWS profile name (default: 'default')
--fsx, -f Show FSx for NetApp ONTAP recommendations
```

<details>
<summary>Example Output</summary>

```bash
$ python ebsight.py -p demo-profile -g -f
Enter EC2 Instance ID: i-0a1b2c3d4e5f6g7h8

🖥️  Analyzing EC2 Instance: i-0a1b2c3d4e5f6g7h8
Name: demo-database-01
================================================================================

💾 Found 7 attached volumes

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h1 (/dev/sda1)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               150.0 GiB                     
   Snapshot Total Size       79.8 GiB                      
   Usage %                   53.2%                         
   Snapshot Count            7                             
   Daily Change Rate         13.31 GiB (8.9%)              
   Total Changed Data        79.8 GiB                      
   Daily Backup Cost         $0.13
   Monthly Backup Cost       $3.99
   Annual Backup Cost        $47.90
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h1
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 150.00 GiB
   Snapshot Size  ██████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 79.83 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h2 (/dev/sdb)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               210.0 GiB                     
   Snapshot Total Size       106.8 GiB                     
   Usage %                   50.8%                         
   Snapshot Count            7                             
   Daily Change Rate         17.79 GiB (8.5%)              
   Total Changed Data        106.8 GiB                     
   Daily Backup Cost         $0.18
   Monthly Backup Cost       $5.34
   Annual Backup Cost        $64.05
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h2
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 210.00 GiB
   Snapshot Size  █████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░ 106.76 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h3 (/dev/sdc)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               2500.0 GiB                    
   Snapshot Total Size       1965.5 GiB                    
   Usage %                   78.6%                         
   Snapshot Count            7                             
   Daily Change Rate         327.58 GiB (13.1%)            
   Total Changed Data        1965.5 GiB                    
   Daily Backup Cost         $3.28
   Monthly Backup Cost       $98.28
   Annual Backup Cost        $1179.30
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h3
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 2500.00 GiB
   Snapshot Size  ███████████████████████████████████████░░░░░░░░░░░ 1965.51 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h4 (/dev/sdd)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               201.0 GiB                     
   Snapshot Total Size       27.5 GiB                      
   Usage %                   13.7%                         
   Snapshot Count            7                             
   Daily Change Rate         4.58 GiB (2.3%)               
   Total Changed Data        27.5 GiB                      
   Daily Backup Cost         $0.05
   Monthly Backup Cost       $1.37
   Annual Backup Cost        $16.50
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h4
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 201.00 GiB
   Snapshot Size  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 27.50 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h5 (/dev/sde)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               50.0 GiB                      
   Snapshot Total Size       19.3 GiB                      
   Usage %                   38.6%                         
   Snapshot Count            7                             
   Daily Change Rate         3.22 GiB (6.4%)               
   Total Changed Data        19.3 GiB                      
   Daily Backup Cost         $0.03
   Monthly Backup Cost       $0.97
   Annual Backup Cost        $11.59
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h5
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 50.00 GiB
   Snapshot Size  ███████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 19.31 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h6 (/dev/sdf)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               203.0 GiB                     
   Snapshot Total Size       53.0 GiB                      
   Usage %                   26.1%                         
   Snapshot Count            7                             
   Daily Change Rate         8.83 GiB (4.4%)               
   Total Changed Data        53.0 GiB                      
   Daily Backup Cost         $0.09
   Monthly Backup Cost       $2.65
   Annual Backup Cost        $31.80
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h6
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 203.00 GiB
   Snapshot Size  █████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 53.00 GiB

📀 Analyzing Volume: vol-0a1b2c3d4e5f6g7h7 (/dev/sdg)
================================================================================
🔍 Found 7 snapshots

   Volume Summary:
   ------------------------------------------------------------
   Metric                    Value                         
   ------------------------------------------------------------
   Volume Size               52.0 GiB                      
   Snapshot Total Size       46.3 GiB                      
   Usage %                   89.0%                         
   Snapshot Count            7                             
   Daily Change Rate         7.72 GiB (14.8%)              
   Total Changed Data        46.3 GiB                      
   Daily Backup Cost         $0.08
   Monthly Backup Cost       $2.32
   Annual Backup Cost        $27.78
   ------------------------------------------------------------

   📊 Size Comparison for vol-0a1b2c3d4e5f6g7h7
   ==============================================================
   Volume Size    ██████████████████████████████████████████████████ 52.00 GiB
   Snapshot Size  ████████████████████████████████████████████░░░░░░ 46.30 GiB

   Volume Analysis Summary:
   ====================================================================================================================================================================================
   Volume ID                 Mount    Size     Used %   P99 IOPS (R/W)        Peak IOPS (R/W)       P99 MBps (R/W)        Peak MBps (R/W)       Queue   
   ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   0a1b2c3d4e5f6g7h1        sda1     150.0    53.2    35/21                 35/21                 1.1/3.0               1.1/3.0               0.59    
   0a1b2c3d4e5f6g7h2        sdb      210.0    50.8    2/1                   2/1                   0.1/0.1               0.1/0.1               0.02    
   0a1b2c3d4e5f6g7h3        sdc      2500.0   78.6    112/26                113/26                5.2/1.3               5.2/1.3               0.85    
   0a1b2c3d4e5f6g7h4        sdd      201.0    13.7    30/0                  30/0                  4.1/0.0               4.1/0.0               0.48    
   0a1b2c3d4e5f6g7h5        sde      50.0     38.6    22/27                 22/27                 1.4/1.3               1.4/1.3               0.36    
   0a1b2c3d4e5f6g7h6        sdf      203.0    26.1    3/18                  3/18                  0.2/0.5               0.2/0.5               0.18    
   0a1b2c3d4e5f6g7h7        sdg      52.0     89.0    0/1                   0/1                   0.0/0.0               0.0/0.0               0.01    
   ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
   TOTALS:                          3366.0            204/94                206/94                12.0/6.1              12.1/6.1         
   ====================================================================================================================================================================================

   📊 FSx for NetApp ONTAP Sizing Recommendations:
   --------------------------------------------------------------------------------
   Total Storage Required (GB):    3366
   Recommended SSD Size (GB):      383  (11.4% of total)
   Sustained IOPS Required:        298
   Peak IOPS Required:             300
   Sustained Throughput (MBps):    18.1
   Peak Throughput (MBps):         18.2
   --------------------------------------------------------------------------------

✅ Analysis completed for all volumes.
```

</details>

## How It Works

### Volume Discovery

- Takes an EC2 instance ID as input
- Identifies all attached EBS volumes
- Retrieves volume metadata and configurations

### Snapshot Analysis

- Leverages the new `FullSnapshotSizeInBytes` field from AWS's API
- Calculates incremental changes between snapshots
- Determines storage efficiency and usage patterns

### Performance Monitoring

Collects CloudWatch metrics for:

- Read/Write IOPS
- Throughput
- Queue lengths
- Analyzes both P99 and peak performance metrics

### Output Formats

- Console-based summary tables
- ASCII visualization graphs
- CSV export for further analysis
- FSx sizing recommendations

## Inspiration from AWS Update

EBSight was developed in response to AWS's introduction of the full snapshot size information feature. This new capability allows for:

- More accurate storage analysis
- Better cost optimization
- Improved capacity planning
- Enhanced snapshot management

### Visual Monitoring

- Use the `--graph` option to visualize performance patterns
- Monitor IOPS and throughput for capacity planning

### Migration Planning

- Utilize FSx recommendations for storage migration projects
- Consider change rates when planning storage solutions

## Requirements

- Python 3.8 or higher
- boto3
- AWS credentials configured
- Appropriate IAM permissions for EC2 and CloudWatch access

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ebsight.git
cd ebsight
```

### 2. Set Up Python Environment

Choose one of these methods:

#### Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

Ensure your AWS credentials are configured using one of these methods:

- AWS CLI: `aws configure`
- Environment variables
- Credentials file (`~/.aws/credentials`)

### 4. Required IAM Permissions

Your AWS user/role needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "ec2:DescribeSnapshots",
                "cloudwatch:GetMetricStatistics"
            ],
            "Resource": "*"
        }
    ]
}
```

### 5. Verify Installation

```bash
# Ensure your virtual environment is activated
python ebsight.py --help
```

Hope this helps someone else.
