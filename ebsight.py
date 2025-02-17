import boto3
import json
import argparse
import csv
from datetime import datetime, timedelta, UTC
from pathlib import Path

def json_datetime_converter(obj):
    """Convert datetime objects to ISO format strings for JSON serialization.
    
    Args:
        obj: Object to convert, expected to be a datetime object
        
    Returns:
        str: ISO formatted datetime string
        
    Raises:
        TypeError: If the object is not a datetime instance
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_to_csv(instance_id, instance_name, volumes_data, output_file):
    """Export volume and snapshot analysis data to a CSV file.
    
    Args:
        instance_id (str): EC2 instance identifier
        instance_name (str): Name tag of the EC2 instance
        volumes_data (list): List of dictionaries containing volume analysis data
        output_file (str): Path to the output CSV file
    """
    with open(output_file, 'w', newline='') as csvfile:
        # Create CSV writer
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow([
            'Instance ID', 'Instance Name', 'Volume ID', 'Device Name',
            'Volume Size (GiB)', 'Total Snapshot Size (GiB)', 'Snapshot Count',
            'Usage Percentage', 'Daily Cost ($)', 'Weekly Cost ($)',
            'Monthly Cost ($)', 'Annual Cost ($)'
        ])
        
        # Write data for each volume
        for volume_data in volumes_data:
            writer.writerow([
                instance_id,
                instance_name,
                volume_data['volume_id'],
                volume_data['device_name'],
                f"{volume_data['volume_size']:.2f}",
                f"{volume_data['total_snapshot_size']:.2f}",
                volume_data['snapshot_count'],
                f"{volume_data['usage_percentage']:.2f}",
                f"{volume_data['daily_cost']:.3f}",
                f"{volume_data['weekly_cost']:.2f}",
                f"{volume_data['monthly_cost']:.2f}",
                f"{volume_data['annual_cost']:.2f}"
            ])

def create_bar(value, max_value, width=50):
    """Create an ASCII bar graph representation.
    
    Args:
        value (float): Current value to represent
        max_value (float): Maximum value for scaling
        width (int, optional): Width of the bar in characters. Defaults to 50.
        
    Returns:
        str: ASCII bar representation using █ for filled and ░ for empty space
    """
    bar_width = int((value / max_value) * width)
    return '█' * bar_width + '░' * (width - bar_width)

def create_volume_graph(volume_data):
    """Generate ASCII-based graphs showing volume and snapshot size comparisons.
    
    Args:
        volume_data (dict): Dictionary containing volume metrics including:
            - volume_id: EBS volume identifier
            - volume_size: Size of the volume in GiB
            - total_snapshot_size: Total size of snapshots in GiB
            - avg_read_ops_p99: 99th percentile of read operations
            - avg_write_ops_p99: 99th percentile of write operations
            - avg_read_ops_peak: Peak read operations
            - avg_write_ops_peak: Peak write operations
    """
    width = 50
    
    # Size comparison
    print(f"\n   📊 Size Comparison for {volume_data['volume_id']}")
    print("   " + "=" * 62)
    
    max_size = max(volume_data['volume_size'], volume_data['total_snapshot_size'])
    
    # Volume size bar
    vol_bar = create_bar(volume_data['volume_size'], max_size, width)
    print(f"   Volume Size    {vol_bar} {volume_data['volume_size']:.2f} GiB")
    
    # Snapshot size bar
    snap_bar = create_bar(volume_data['total_snapshot_size'], max_size, width)
    print(f"   Snapshot Size  {snap_bar} {volume_data['total_snapshot_size']:.2f} GiB")
    
    # IOPS comparison
    if volume_data.get('avg_read_ops_p99', 0) > 0 or volume_data.get('avg_write_ops_p99', 0) > 0:
        print(f"\n   📈 IOPS Breakdown")
        print("   " + "=" * 62)
        
        max_iops = max(
            volume_data.get('avg_read_ops_p99', 0),
            volume_data.get('avg_write_ops_p99', 0),
            volume_data.get('avg_read_ops_peak', 0),
            volume_data.get('avg_write_ops_peak', 0)
        )
        
        if max_iops > 0:
            # P99 IOPS bars
            read_bar = create_bar(volume_data.get('avg_read_ops_p99', 0), max_iops, width)
            print(f"   P99 Read     {read_bar} {volume_data.get('avg_read_ops_p99', 0):.1f}")
            
            write_bar = create_bar(volume_data.get('avg_write_ops_p99', 0), max_iops, width)
            print(f"   P99 Write    {write_bar} {volume_data.get('avg_write_ops_p99', 0):.1f}")
            
            # Peak IOPS bars
            read_peak_bar = create_bar(volume_data.get('avg_read_ops_peak', 0), max_iops, width)
            print(f"   Peak Read    {read_peak_bar} {volume_data.get('avg_read_ops_peak', 0):.1f}")
            
            write_peak_bar = create_bar(volume_data.get('avg_write_ops_peak', 0), max_iops, width)
            print(f"   Peak Write   {write_peak_bar} {volume_data.get('avg_write_ops_peak', 0):.1f}")

def get_volume_metrics(ec2_client, cloudwatch, volume_id):
    """Retrieve CloudWatch metrics for an EBS volume.
    
    Args:
        ec2_client: Boto3 EC2 client
        cloudwatch: Boto3 CloudWatch client
        volume_id (str): EBS volume identifier
        
    Returns:
        dict: Dictionary containing metrics including:
            - ReadOps_p99: 99th percentile of read operations
            - WriteOps_p99: 99th percentile of write operations
            - ReadOps_peak: Peak read operations
            - WriteOps_peak: Peak write operations
            - ReadThroughput_p99: 99th percentile of read throughput
            - WriteThroughput_p99: 99th percentile of write throughput
            - ReadThroughput_peak: Peak read throughput
            - WriteThroughput_peak: Peak write throughput
            - QueueLength_p99: 99th percentile of queue length
    """
    try:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)
        period = 600  # 10-minute periods
        
        metrics = {
            'ReadOps': {
                'MetricName': 'VolumeReadOps',
                'Namespace': 'AWS/EBS',
                'Dimensions': [{'Name': 'VolumeId', 'Value': volume_id}],
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'ExtendedStatistics': ['p99', 'p99.9']
            },
            'WriteOps': {
                'MetricName': 'VolumeWriteOps',
                'Namespace': 'AWS/EBS',
                'Dimensions': [{'Name': 'VolumeId', 'Value': volume_id}],
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'ExtendedStatistics': ['p99', 'p99.9']
            },
            'ReadThroughput': {
                'MetricName': 'VolumeReadBytes',
                'Namespace': 'AWS/EBS',
                'Dimensions': [{'Name': 'VolumeId', 'Value': volume_id}],
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'ExtendedStatistics': ['p99', 'p99.9']
            },
            'WriteThroughput': {
                'MetricName': 'VolumeWriteBytes',
                'Namespace': 'AWS/EBS',
                'Dimensions': [{'Name': 'VolumeId', 'Value': volume_id}],
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'ExtendedStatistics': ['p99', 'p99.9']
            },
            'QueueLength': {
                'MetricName': 'VolumeQueueLength',
                'Namespace': 'AWS/EBS',
                'Dimensions': [{'Name': 'VolumeId', 'Value': volume_id}],
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'ExtendedStatistics': ['p99']
            }
        }
        
        results = {}
        for metric_name, metric_params in metrics.items():
            response = cloudwatch.get_metric_statistics(**metric_params)
            if response['Datapoints']:
                if metric_name in ['ReadOps', 'WriteOps']:
                    # Convert to operations per second
                    results[f"{metric_name}_p99"] = max(point['ExtendedStatistics']['p99'] for point in response['Datapoints']) / period
                    results[f"{metric_name}_peak"] = max(point['ExtendedStatistics']['p99.9'] for point in response['Datapoints']) / period
                elif metric_name in ['ReadThroughput', 'WriteThroughput']:
                    # Convert to MBps (bytes per period to MB per second)
                    results[f"{metric_name}_p99"] = max(point['ExtendedStatistics']['p99'] for point in response['Datapoints']) / period / (1024 * 1024)
                    results[f"{metric_name}_peak"] = max(point['ExtendedStatistics']['p99.9'] for point in response['Datapoints']) / period / (1024 * 1024)
                else:
                    results[f"{metric_name}_p99"] = max(point['ExtendedStatistics']['p99'] for point in response['Datapoints'])
            else:
                results[f"{metric_name}_p99"] = 0
                if metric_name in ['ReadOps', 'WriteOps', 'ReadThroughput', 'WriteThroughput']:
                    results[f"{metric_name}_peak"] = 0
        
        return results
    except Exception as e:
        print(f"   ⚠️  Warning: Could not fetch metrics: {str(e)}")
        return {
            'ReadOps_p99': 0, 'WriteOps_p99': 0,
            'ReadOps_peak': 0, 'WriteOps_peak': 0,
            'ReadThroughput_p99': 0, 'WriteThroughput_p99': 0,
            'ReadThroughput_peak': 0, 'WriteThroughput_peak': 0,
            'QueueLength_p99': 0
        }

def print_consolidated_summary(volumes_data, show_fsx_recommendations=False):
    """Print a consolidated summary of all analyzed volumes.
    
    Args:
        volumes_data (list): List of dictionaries containing volume analysis data
        show_fsx_recommendations (bool, optional): Whether to show FSx sizing 
            recommendations. Defaults to False.
    """
    if not volumes_data:
        return
        
    print("\n   Volume Analysis Summary:")
    print("   " + "=" * 180)
    print(f"   {'Volume ID':<15} {'Mount':<8} {'Size':<12} {'Used %':<8} "
          f"{'P99 IOPS (R/W)':<25} {'Peak IOPS (R/W)':<25} "
          f"{'P99 MBps (R/W)':<25} {'Peak MBps (R/W)':<25} {'Queue':<8}")
    print("   " + "-" * 180)
    
    total_size = 0
    total_read_iops_p99 = 0
    total_write_iops_p99 = 0
    total_read_iops_peak = 0
    total_write_iops_peak = 0
    total_read_mbps_p99 = 0
    total_write_mbps_p99 = 0
    total_read_mbps_peak = 0
    total_write_mbps_peak = 0
    
    for vol in volumes_data:
        vol_id = vol['volume_id'].split('-')[-1]
        usage_pct = (vol['total_snapshot_size'] / vol['volume_size'] * 100) if vol['volume_size'] > 0 else 0
        
        # Update totals
        total_size += vol['volume_size']
        total_read_iops_p99 += vol['ReadOps_p99']
        total_write_iops_p99 += vol['WriteOps_p99']
        total_read_iops_peak += vol['ReadOps_peak']
        total_write_iops_peak += vol['WriteOps_peak']
        total_read_mbps_p99 += vol['ReadThroughput_p99']
        total_write_mbps_p99 += vol['WriteThroughput_p99']
        total_read_mbps_peak += vol['ReadThroughput_peak']
        total_write_mbps_peak += vol['WriteThroughput_peak']
        
        # Format IOPS and throughput with consistent spacing
        p99_iops = f"{vol['ReadOps_p99']:>7.0f}/{vol['WriteOps_p99']:<7.0f}"
        peak_iops = f"{vol['ReadOps_peak']:>7.0f}/{vol['WriteOps_peak']:<7.0f}"
        p99_mbps = f"{vol['ReadThroughput_p99']:>7.1f}/{vol['WriteThroughput_p99']:<7.1f}"
        peak_mbps = f"{vol['ReadThroughput_peak']:>7.1f}/{vol['WriteThroughput_peak']:<7.1f}"
        
        print(f"   {vol_id:<15} "
              f"{vol['device_name'][-3:]:<8} "
              f"{vol['volume_size']:<12.1f} "
              f"{usage_pct:<8.1f} "
              f"{p99_iops:^25} "
              f"{peak_iops:^25} "
              f"{p99_mbps:^25} "
              f"{peak_mbps:^25} "
              f"{vol['QueueLength_p99']:<8.2f}")
    
    print("   " + "-" * 180)
    # Format totals with consistent spacing
    total_p99_iops = f"{total_read_iops_p99:>7.0f}/{total_write_iops_p99:<7.0f}"
    total_peak_iops = f"{total_read_iops_peak:>7.0f}/{total_write_iops_peak:<7.0f}"
    total_p99_mbps = f"{total_read_mbps_p99:>7.1f}/{total_write_mbps_p99:<7.1f}"
    total_peak_mbps = f"{total_read_mbps_peak:>7.1f}/{total_write_mbps_peak:<7.1f}"
    
    print(f"   {'TOTALS:':<23} {total_size:<12.1f} {'':8} "
          f"{total_p99_iops:^25} "
          f"{total_peak_iops:^25} "
          f"{total_p99_mbps:^25} "
          f"{total_peak_mbps:^25}")
    print("   " + "=" * 180)
    
    if show_fsx_recommendations:
        # Calculate recommended SSD size based on daily change rate
        total_daily_change = sum(vol.get('avg_daily_change', 0) for vol in volumes_data)
        daily_change_percent = (total_daily_change / total_size * 100) if total_size > 0 else 0
        
        print("\n   📊 FSx for NetApp ONTAP Sizing Recommendations:")
        print("   " + "-" * 80)
        print(f"   Total Storage Required (GB):    {total_size:.0f}")
        print(f"   Recommended SSD Size (GB):      {total_daily_change:.0f}  ({daily_change_percent:.1f}% of total)")
        print(f"   Sustained IOPS Required:        {(total_read_iops_p99 + total_write_iops_p99):.0f}")
        print(f"   Peak IOPS Required:             {(total_read_iops_peak + total_write_iops_peak):.0f}")
        print(f"   Sustained Throughput (MBps):    {(total_read_mbps_p99 + total_write_mbps_p99):.1f}")
        print(f"   Peak Throughput (MBps):         {(total_read_mbps_peak + total_write_mbps_peak):.1f}")
        print("   " + "-" * 80)

def calculate_snapshot_costs(snapshot_size_gib):
    """Calculate estimated AWS costs for EBS snapshots.
    
    Args:
        snapshot_size_gib (float): Size of snapshots in GiB
        
    Returns:
        dict: Dictionary containing cost estimates:
            - daily_cost: Estimated cost per day
            - weekly_cost: Estimated cost per week
            - monthly_cost: Estimated cost per month
            - annual_cost: Estimated cost per year
            
    Note:
        Costs are calculated using us-east-1 pricing ($0.05 per GB-month)
    """
    # AWS EBS snapshot pricing (varies by region, using us-east-1 as example)
    SNAPSHOT_COST_PER_GB_MONTH = 0.05  # $0.05 per GB-month
    
    # Calculate costs for different time periods
    daily_cost = (snapshot_size_gib * SNAPSHOT_COST_PER_GB_MONTH) / 30  # Cost per day
    weekly_cost = daily_cost * 7
    monthly_cost = snapshot_size_gib * SNAPSHOT_COST_PER_GB_MONTH
    annual_cost = monthly_cost * 12
    
    return {
        'daily_cost': daily_cost,
        'weekly_cost': weekly_cost,
        'monthly_cost': monthly_cost,
        'annual_cost': annual_cost
    }

def analyze_volume_snapshots(ec2, cloudwatch, volume_id, volume_name, verbose=False, show_graphs=False):
    """Analyze EBS volume snapshots and performance metrics.
    
    Args:
        ec2: Boto3 EC2 client
        cloudwatch: Boto3 CloudWatch client
        volume_id (str): EBS volume identifier
        volume_name (str): Name or device name of the volume
        verbose (bool, optional): Whether to show detailed output. Defaults to False.
        show_graphs (bool, optional): Whether to show ASCII graphs. Defaults to False.
        
    Returns:
        dict: Dictionary containing comprehensive volume analysis including:
            - volume_id: EBS volume identifier
            - device_name: Device name of the volume
            - volume_size: Size of the volume in GiB
            - total_snapshot_size: Total size of snapshots in GiB
            - snapshot_count: Number of snapshots
            - usage_percentage: Percentage of volume used
            - avg_daily_change: Average daily data change rate
            - avg_daily_change_percent: Percentage of daily change
            - total_change: Total data changed
            - daily_cost: Estimated daily cost
            - weekly_cost: Estimated weekly cost
            - monthly_cost: Estimated monthly cost
            - annual_cost: Estimated annual cost
            - Various performance metrics (IOPS, throughput, queue length)
    """
    print(f"\n📀 Analyzing Volume: {volume_id} ({volume_name})")
    print("=" * 80)
    
    # Get volume information first
    volume_info = ec2.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]
    volume_size = volume_info['Size']  # Size in GiB
    
    # Fetch snapshots for this volume
    snapshots = ec2.describe_snapshots(
        Filters=[{'Name': 'volume-id', 'Values': [volume_id]}],
        OwnerIds=['self']
    )["Snapshots"]
    
    # Sort snapshots by creation date
    volume_snapshots = sorted(snapshots, key=lambda x: x["StartTime"])
    
    if not volume_snapshots:
        print(f"   No snapshots found for volume {volume_id}")
        return None
    
    print(f"🔍 Found {len(volume_snapshots)} snapshots")
    
    # Process snapshots and calculate changes
    snapshot_data = []

    for snap in volume_snapshots:
        size_gib = snap.get('VolumeSize', 0)
        actual_size_gib = float(snap.get('FullSnapshotSizeInBytes', 0)) / (1024 ** 3)
        
        snapshot_data.append({
            'id': snap['SnapshotId'],
            'time': snap['StartTime'],
            'size_gib': size_gib,
            'actual_size_gib': actual_size_gib,
            'description': snap.get('Description', 'No description')
        })

    # Use the latest snapshot's actual size as the total snapshot size
    total_snapshot_size = snapshot_data[-1]['actual_size_gib'] if snapshot_data else 0
    
    # Calculate changes between snapshots
    if len(snapshot_data) >= 2:
        latest_snapshot = snapshot_data[-1]
        first_snapshot = snapshot_data[0]
        
        # If data size has increased
        if latest_snapshot['actual_size_gib'] > first_snapshot['actual_size_gib']:
            total_change = latest_snapshot['actual_size_gib']
        else:
            # If data size has decreased or stayed same
            total_change = first_snapshot['actual_size_gib']
    else:
        total_change = snapshot_data[0]['actual_size_gib'] if snapshot_data else 0
    
    # Calculate the total days between first and last snapshot
    if len(snapshot_data) >= 2:
        first_snapshot_time = snapshot_data[0]['time']
        last_snapshot_time = snapshot_data[-1]['time']
        total_days = (last_snapshot_time - first_snapshot_time).days
        if total_days == 0:  # Handle same-day snapshots
            total_days = 1
    else:
        total_days = 1  # Default to 1 day if only one snapshot exists

    # Calculate average daily change
    avg_daily_change = total_change / total_days if total_days > 0 else 0
    avg_daily_change_percent = (avg_daily_change / volume_size * 100) if volume_size > 0 else 0
    usage_percentage = (total_snapshot_size/volume_size*100) if volume_size > 0 else 0
    
    # Calculate costs based on actual snapshot size
    costs = calculate_snapshot_costs(total_snapshot_size)
    
    if verbose:
        print(f"\n   📈 Volume Summary:")
        print(f"      Volume Size: {volume_size:.2f} GiB")
        print(f"      Total Size of All Snapshots: {total_snapshot_size:.2f} GiB")
        print(f"      Percentage of Original Volume: {usage_percentage:.2f}%")
        print(f"      Number of Snapshots: {len(volume_snapshots)}")
        print(f"      Average Daily Change: {avg_daily_change:.2f} GiB/day ({avg_daily_change_percent:.1f}%)")
        print(f"      Total Data Changed: {total_change:.2f} GiB")
        print(f"\n   💰 Cost Estimates:")
        print(f"      Daily Cost: ${costs['daily_cost']:.2f}")
        print(f"      Weekly Cost: ${costs['weekly_cost']:.2f}")
        print(f"      Monthly Cost: ${costs['monthly_cost']:.2f}")
        print(f"      Annual Cost: ${costs['annual_cost']:.2f}")
    else:
        # Compact tabulated output
        print("\n   Volume Summary:")
        print("   " + "-" * 60)  # Reduced width
        print(f"   {'Metric':<25} {'Value':<30}")  # Removed Cost Impact column
        print("   " + "-" * 60)  # Reduced width
        print(f"   {'Volume Size':<25} {f'{volume_size:.1f} GiB':<30}")
        print(f"   {'Snapshot Total Size':<25} {f'{total_snapshot_size:.1f} GiB':<30}")
        print(f"   {'Usage %':<25} {f'{usage_percentage:.1f}%':<30}")
        print(f"   {'Snapshot Count':<25} {len(volume_snapshots):<30}")
        print(f"   {'Daily Change Rate':<25} {f'{avg_daily_change:.2f} GiB ({avg_daily_change_percent:.1f}%)':<30}")
        print(f"   {'Total Changed Data':<25} {f'{total_change:.1f} GiB':<30}")
        print(f"   {'Daily Backup Cost':<25} ${costs['daily_cost']:.2f}")
        print(f"   {'Monthly Backup Cost':<25} ${costs['monthly_cost']:.2f}")
        print(f"   {'Annual Backup Cost':<25} ${costs['annual_cost']:.2f}")
        print("   " + "-" * 60)  # Reduced width
    
    if show_graphs:
        create_volume_graph({
            'volume_id': volume_id,
            'volume_size': volume_size,
            'total_snapshot_size': total_snapshot_size,
            'daily_cost': 0,
            'weekly_cost': 0,
            'monthly_cost': 0,
            'annual_cost': 0
        })
    
    # Get volume metrics using passed cloudwatch client
    metrics = get_volume_metrics(ec2, cloudwatch, volume_id)
    
    return {
        'volume_id': volume_id,
        'device_name': volume_name,
        'volume_size': volume_size,
        'total_snapshot_size': total_snapshot_size,
        'snapshot_count': len(volume_snapshots),
        'usage_percentage': usage_percentage,
        'avg_daily_change': avg_daily_change,
        'avg_daily_change_percent': avg_daily_change_percent,
        'total_change': total_change,
        'daily_cost': costs['daily_cost'],
        'weekly_cost': costs['weekly_cost'],
        'monthly_cost': costs['monthly_cost'],
        'annual_cost': costs['annual_cost'],
        'ReadOps_p99': metrics['ReadOps_p99'],
        'WriteOps_p99': metrics['WriteOps_p99'],
        'ReadOps_peak': metrics['ReadOps_peak'],
        'WriteOps_peak': metrics['WriteOps_peak'],
        'QueueLength_p99': metrics['QueueLength_p99'],
        'ReadThroughput_p99': metrics['ReadThroughput_p99'],
        'WriteThroughput_p99': metrics['WriteThroughput_p99'],
        'ReadThroughput_peak': metrics['ReadThroughput_peak'],
        'WriteThroughput_peak': metrics['WriteThroughput_peak']
    }

# Main execution
def main():
    """Main execution function for EBSight.
    
    Handles command-line argument parsing and orchestrates the analysis of EC2
    instance volumes and their snapshots. Supports various output formats and
    analysis options through command-line flags.
    
    Command-line options:
        --verbose, -v: Show detailed snapshot information
        --csv, -c: Export results to CSV
        --graph, -g: Show ASCII graphs
        --profile, -p: AWS profile name (default: 'default')
        --fsx, -f: Show FSx for NetApp ONTAP sizing recommendations
    """
    # ASCII art logo
    logo = """
 ███████╗██████╗ ███████╗██╗ ██████╗ ██╗  ██╗████████╗
 ██╔════╝██╔══██╗██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝
 █████╗  ██████╔╝███████╗██║██║  ███╗███████║   ██║   
 ██╔══╝  ██╔══██╗╚════██║██║██║   ██║██╔══██║   ██║   
 ███████╗██████╔╝███████║██║╚██████╔╝██║  ██║   ██║   
 ╚══════╝╚═════╝ ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
                                                       
 📊 Intelligent EBS Volume Analyzer
    """
    
    parser = argparse.ArgumentParser(
        description=logo + '\nAnalyze EC2 instance volumes and their snapshots',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed snapshot information')
    parser.add_argument('--csv', '-c', action='store_true', help='Export results to CSV')
    parser.add_argument('--graph', '-g', action='store_true', help='Show ASCII graphs')
    parser.add_argument('--profile', '-p', default='default', help='AWS profile name')
    parser.add_argument('--fsx', '-f', action='store_true', help='Show FSx for NetApp ONTAP sizing recommendations')
    args = parser.parse_args()
    
    try:
        # Create AWS session with specified profile
        session = boto3.Session(profile_name=args.profile)
        ec2 = session.client("ec2")
        cloudwatch = session.client("cloudwatch")
        
        # Get instance ID from user
        instance_id = input("Enter EC2 Instance ID: ")
        
        try:
            # Get instance details
            instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
            
            print(f"\n🖥️  Analyzing EC2 Instance: {instance_id}")
            print(f"Name: {next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')}")
            print("=" * 80)
            
            # Get all volumes attached to the instance
            volumes = instance.get('BlockDeviceMappings', [])
            
            if not volumes:
                print("No volumes found attached to this instance.")
                return
            
            print(f"\n💾 Found {len(volumes)} attached volumes")
            
            volumes_data = []
            for volume in volumes:
                volume_id = volume['Ebs']['VolumeId']
                device_name = volume['DeviceName']
                volume_data = analyze_volume_snapshots(ec2, cloudwatch, volume_id, device_name, 
                                                    args.verbose, args.graph)
                if volume_data:
                    volumes_data.append(volume_data)
            
            if volumes_data:
                print_consolidated_summary(volumes_data, args.fsx)
            
            if args.csv and volumes_data:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"snapshot_analysis_{instance_id}_{timestamp}.csv"
                instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'No Name')
                export_to_csv(instance_id, instance_name, volumes_data, output_file)
                print(f"\n📊 CSV report exported to: {output_file}")
            
            print("\n✅ Analysis completed for all volumes.")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease ensure your AWS credentials are properly configured:")
        print("1. Check ~/.aws/credentials file")
        print("2. Check ~/.aws/config file")
        print("3. Use --profile option to specify a different profile")
        print("\nExample: python blockdiffchecker.py --profile your-profile-name")

if __name__ == "__main__":
    main()
