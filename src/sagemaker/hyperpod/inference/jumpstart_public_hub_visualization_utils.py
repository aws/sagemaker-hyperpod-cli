# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

"""Notebook visualization utilities for Models in JumpStart Public Hub."""
from __future__ import absolute_import

import time
import boto3
import itables
import pandas
import logging
import json
from botocore.config import Config
from ipywidgets import Button, Output
from IPython.display import display


class ModelDataLoader:
    """Handles progressive loading of model data from SageMaker Hub."""
    
    TIMEOUT_SECONDS = 30
    MAX_RESULTS_PER_CALL = 100
    
    def __init__(self, region: str, hub_name: str = "SageMakerPublicHub"):
        config = Config(region_name=region, retries={"max_attempts": 10, "mode": "adaptive"})
        self.client = boto3.client("sagemaker", config=config)
        self.hub_name = hub_name
        self.all_data = []
        self.next_token = None
        self.table_output = None
        self.load_button = None
    
    def load_initial_data(self, limit: int = 100):
        """Load first batch of models and display progressive table."""
        batch_data = self._get_batch(limit)
        self.all_data = batch_data["data"]
        self.next_token = batch_data["next_token"]
        self._display_progressive_table()
    
    def _get_batch(self, limit: int = 100):
        """Get a batch of model data with pagination and timeout."""
        model_summaries = []
        current_token = self.next_token
        start_time = time.time()
        
        try:
            while (len(model_summaries) < limit and 
                   (time.time() - start_time) < self.TIMEOUT_SECONDS):
                
                params = {
                    "HubName": self.hub_name,
                    "HubContentType": "Model",
                    "MaxResults": min(self.MAX_RESULTS_PER_CALL, limit - len(model_summaries))
                }
                if current_token:
                    params["NextToken"] = current_token
                
                response = self.client.list_hub_contents(**params)
                batch_summaries = [
                    self._get_model_summary(summary) 
                    for summary in response["HubContentSummaries"]
                ]
                model_summaries.extend(batch_summaries)
                
                current_token = response.get("NextToken")
                if not current_token:
                    break
            
            if (time.time() - start_time) >= self.TIMEOUT_SECONDS:
                logging.debug(f"Retrieved {len(model_summaries)} models in {self.TIMEOUT_SECONDS} seconds. There may be more models to list, press Load More Models button to continue loading.")
            
            return {"data": model_summaries, "next_token": current_token}
            
        except Exception as e:
            print(f"Error fetching models: {e}")
            return {"data": model_summaries, "next_token": current_token}
    
    def _display_progressive_table(self):
        """Display table with optional load more button."""
        if not self.all_data:
            print("No models to display")
            return
        
        self._create_and_display_table()
        self._create_load_button()
    
    def _create_load_button(self):
        """Create and display load more button if needed."""
        if self.next_token:
            self.load_button = Button(description="Load More Models")
            self.load_button.on_click(lambda b: self._load_more())
            display(self.load_button)
    
    def _create_and_display_table(self):
        """Create and display the data table."""
        self.table_output = Output()
        display(self.table_output)
        
        try:
            with self.table_output:
                self.table_output.clear_output(wait=True)
                interactive_view(self.all_data)
        except Exception as e:
            print(f"Error displaying table: {e}")
    
    def _load_more(self):
        """Load next batch and update consolidated table."""
        if not self.next_token:
            print("No more models to load")
            return
        
        self._set_loading_state()
        self._fetch_and_update_data()
        self._update_button_state()
    
    def _set_loading_state(self):
        """Set button to loading state."""
        if self.load_button:
            self.load_button.disabled = True
            self.load_button.description = "Loading..."
    
    def _fetch_and_update_data(self):
        """Fetch new data and update table."""
        batch_data = self._get_batch()
        self.next_token = batch_data["next_token"]
        self.all_data.extend(batch_data["data"])
        
        with self.table_output:
            self.table_output.clear_output(wait=True)
            interactive_view(self.all_data)
    
    def _update_button_state(self):
        """Update button state based on data availability."""
        if not self.load_button:
            return
            
        if self.next_token:
            self.load_button.disabled = False
            self.load_button.description = "Load More Models"
        else:
            self.load_button.description = "All Models Loaded"
    
    def _get_model_summary(self, full_summary):
        """Extract relevant model information."""
        keywords = full_summary["HubContentSearchKeywords"]
        model_type = self._determine_model_type(keywords, full_summary["HubContentName"])
        
        return {
            "Model Id": full_summary["HubContentName"],
            "Model Display Name": full_summary["HubContentDisplayName"],
            "Model Type": model_type,
            "Model Description": full_summary["HubContentDescription"],
            "Search Keywords": keywords,
            "Deployment Configs": self._create_config_link(full_summary["HubContentName"]),
        }
    
    def _determine_model_type(self, keywords, model_id):
        """Determine model type from keywords or hub document."""
        if "@model-type:proprietary" in keywords:
            return "Proprietary"
        elif "@model-type:open_weights" in keywords:
            return "Open"
        else:
            # Check if gated via hub content document
            hub_doc = self._get_hub_document(model_id)
            return "Gated" if '"GatedBucket": true' in hub_doc else "Open"
    
    def _get_hub_document(self, model_id):
        """Get hub content document for model."""
        return self.client.describe_hub_content(
            HubName=self.hub_name, 
            HubContentType="Model", 
            HubContentName=model_id
        )["HubContentDocument"]
    
    def _get_supported_instance_types(self, model_id):
        """Extract supported instance types from hub document."""
        try:
            hub_doc = self._get_hub_document(model_id)
            doc_data = json.loads(hub_doc)
            
            supported_types = doc_data.get("SupportedInferenceInstanceTypes", [])
            default_type = doc_data.get("DefaultInferenceInstanceType")
            
            if default_type and default_type in supported_types:
                supported_types = [default_type] + [t for t in supported_types if t != default_type]
            
            return {"types": supported_types, "default": default_type, "error": None}
        except Exception as e:
            return {"types": [], "default": None, "error": str(e)}
    
    def _create_config_link(self, model_id):
        """Create deployment config display using collapsible details for all environments."""
        return f'<details><summary style="color: #007bff; cursor: pointer;">View SDK Config</summary><pre style="font-size: 10px; background: #f5f5f5; padding: 5px; margin: 5px 0;">{self._generate_deployment_config(model_id)}</pre></details>'
    
    def _generate_deployment_config(self, model_id):
        """Generate deployment configuration code for a model."""
        instance_data = self._get_supported_instance_types(model_id)
        supported_types = instance_data["types"]
        default_type = instance_data["default"]
        error = instance_data["error"]

        if error:
            instance_type = '<ENTER-INSTANCE-TYPE>'
            types_comment = ""
        else:
            instance_type = default_type if default_type else '\<ENTER-INSTANCE-TYPE\>'
            types_comment = self._format_instance_types_comment(supported_types)
        
        config_code = f'''# Deployment configuration for {model_id}
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model, Server, SageMakerEndpoint
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

{types_comment}

# Create configs
model = Model(
    model_id='{model_id}',
)
server = Server(
    instance_type='{instance_type}',
)

# Default endpoint name using model_id, modify as desired
endpoint_name = SageMakerEndpoint(name='{model_id}')

# Create endpoint spec
js_endpoint = HPJumpStartEndpoint(
    model=model,
    server=server,
    sage_maker_endpoint=endpoint_name,
)

# Deploy the endpoint
js_endpoint.create()'''
        return config_code
    
    def _format_instance_types_comment(self, supported_types):
        """Format instance types comment with line breaks for better readability."""
        if not supported_types:
            return "# No supported instance types found"
        
        if len(supported_types) <= 5:
            return f"# Supported instance types: {', '.join(supported_types)}"
        
        # For more than 5 instance types, format with newlines every 5 types
        comment_lines = ["# Supported instance types:"]
        for i in range(0, len(supported_types), 5):
            batch = supported_types[i:i+5]
            comment_lines.append(f"#   {', '.join(batch)}")
        
        return '\n'.join(comment_lines)


def get_all_public_hub_model_data(region: str):
    """Load and display SageMaker public hub models with progressive loading."""
    loader = ModelDataLoader(region)
    loader.load_initial_data()


def interactive_view(tabular_data: list):
    """Display interactive table in Jupyter notebook."""
    if not tabular_data:
        return
    
    _configure_itables()
    df = pandas.DataFrame(tabular_data)
    styled_df = _style_dataframe(df)
    layout = _get_table_layout(len(tabular_data))
    
    itables.show(styled_df, layout=layout, allow_html=True)


def _configure_itables():
    """Configure itables for notebook display."""
    itables.init_notebook_mode(all_interactive=True)
    itables.options.allow_html = True
    

def _style_dataframe(df):
    """Apply styling to dataframe."""
    return df.style.set_properties(**{"text-align": "left"}).set_table_styles(
        [{"selector": "th", "props": [("text-align", "left")]}]
    )


def _get_table_layout(data_length):
    """Get appropriate table layout based on data size."""
    return {} if data_length > 10 else {"topStart": None, "topEnd": "search"}