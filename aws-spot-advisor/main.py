import subprocess
import requests
from typing import List, Dict, Any
import config


def _build_command(region: str) -> List[str]:
    """
    Builds the ec2-instance-selector command with arguments from config.py
    and the specified region.
    """
    command = ["./ec2-instance-selector"]

    # Add arguments from ec2_instance_selector_args
    for key, value in config.ec2_instance_selector_args.items():
        command.append(f"--{key}")
        command.append(str(value))

    # Add arguments from ec2_instance_selector_common_args
    for key, value in config.ec2_instance_selector_common_args.items():
        command.append(f"--{key}")
        command.append(str(value))

    # Add the region argument
    command.append("--region")
    command.append(region)

    return command


def _parse_output(output: str) -> List[Dict[str, Any]]:
    """
    Parses the table-wide output of ec2-instance-selector and returns a list of dictionaries.
    """
    lines = output.strip().split('\n')
    if len(lines) < 3:
        return []  # Not enough lines for header, separator, and data

    # Skip the NOTE line if it exists
    start_index = 0
    if lines[0].startswith("NOTE:"):
        start_index = 1

    header_line = lines[start_index]
    data_lines = lines[start_index + 2:]  # Skip header and separator line

    headers = [h.strip() for h in header_line.split('  ') if h.strip()]
    
    parsed_data = []
    for line in data_lines:
        if not line.strip():
            continue
        
        # Split by multiple spaces to handle variable spacing
        values = [v.strip() for v in line.split('  ') if v.strip()]
        
        # Ensure values match headers, pad with None if necessary
        row_data = {}
        for i, header in enumerate(headers):
            row_data[header] = values[i] if i < len(values) else None
        parsed_data.append(row_data)
    
    return parsed_data


def _fetch_interruption_data(url: str) -> Dict[str, Any]:
    """
    Fetches and parses the spot interruption data from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching interruption data from {url}: {e}")
        return {}


def main():
    all_regions_data = {}
    interruption_data = _fetch_interruption_data("https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json")
    # print(f"Raw interruption data: {interruption_data}") # Debug print

    for region_code, region_name in config.aws_region.items():
        print(f"Fetching data for region: {region_code} ({region_name})...")
        command = _build_command(region_code)
        
        try:
            # Execute the command
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
            output = process.stdout
            
            # Parse the output
            parsed_result = _parse_output(output)
            
            # Add interruption frequency data
            region_interruption_data = interruption_data.get("spot_advisor", {}).get(region_code, {})
            # print(f"Region interruption data for {region_code}: {region_interruption_data}")
            # print(f"Keys in region_interruption_data: {region_interruption_data.keys()}")

            for instance in parsed_result:
                instance_type = instance.get("Instance Type")
                # print(f"Processing instance type: {instance_type}") # Debug print
                if instance_type:
                    # Attempt to get interruption frequency using the full instance type under 'Linux'
                    interruption_frequency = region_interruption_data.get("Linux", {}).get(instance_type, {}).get("r", None)
                    savings_over_ondemand = region_interruption_data.get("Linux", {}).get(instance_type, {}).get("s", None)
                    instance["Savings over On-Demand"] = savings_over_ondemand

                    if interruption_frequency == 0:
                        instance["Interruption Frequency"] = "<5%"
                    elif interruption_frequency == 1:
                        instance["Interruption Frequency"] = "5-10%"
                    elif interruption_frequency == 2:
                        instance["Interruption Frequency"] = "10-15%"
                    elif interruption_frequency == 3:
                        instance["Interruption Frequency"] = "15-20%"
                    elif interruption_frequency == 4:
                        instance["Interruption Frequency"] = ">20%"
                    else:
                        instance["Interruption Frequency"] = "N/A"
                else:
                    instance["Interruption Frequency"] = "N/A"

            all_regions_data[region_code] = parsed_result
            print(f"Successfully fetched {len(parsed_result)} instances for {region_name}.")

        except subprocess.CalledProcessError as e:
            print(f"Error executing command for {region_name}: {e}")
            print(f"Stderr: {e.stderr}")
        except Exception as e:
            print(f"An unexpected error occurred for {region_name}: {e}")

    # You can now work with all_regions_data
    # For demonstration, print the collected data
    from tabulate import tabulate

    print("\n--- Collected Data ---")
    for region_code, instances in all_regions_data.items():
        # Get the correct region name from config.aws_region using the region_code
        current_region_name = config.aws_region.get(region_code, region_code)
        print(f"\nRegion: {region_code} ({current_region_name})")
        if instances:
            # Define the desired columns from config
            desired_columns = config.output_columns
            
            # Filter instances to include only desired columns
            filtered_instances = []
            for instance in instances:
                filtered_instance = {col: instance.get(col) for col in desired_columns}
                filtered_instances.append(filtered_instance)

            # Extract headers from the filtered instances
            headers = desired_columns
            # Convert list of dicts to list of lists for tabulate
            table_data = [list(instance.values()) for instance in filtered_instances]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
        else:
            print("No instances found for this region.")

if __name__ == "__main__":
    main()
