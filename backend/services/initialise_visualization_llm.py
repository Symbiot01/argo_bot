# services/initialise_visualization_llm.py

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, Any, Optional, List
import json
import os
import pandas as pd
from datetime import datetime
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualizationLLMService:
    """Service for handling visualization decisions and HTML response generation"""
    
    def __init__(self):
        self.llm = None
        self.visualization_prompt = None
        self.html_response_prompt = None
        self.initialize_llm()
        self.setup_prompts()
    
    def initialize_llm(self):
        """Initialize the Google Gemini LLM"""
        try:
            # Use Gemini Pro for better reasoning capabilities
            self.llm = ChatGoogleGenerativeAI(
                model = config.LLM_MODEL,
                temperature=0.1,  # Low temperature for consistent decisions
                max_tokens=2048
            )
            logger.info("Visualization LLM initialized successfully with Gemini Pro")
        except Exception as e:
            logger.error(f"Error initializing Visualization LLM: {e}")
            raise
    
    def setup_prompts(self):
        """Setup prompts for visualization decisions and HTML generation"""
        
        # Prompt for deciding whether to create visualizations
        self.visualization_decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data visualization analyst for oceanographic data. 
Your task is to analyze user queries and SQL query results to determine if visualizations would be helpful.

DECISION CRITERIA:
1. RECOMMEND visualizations for:
   - Geographic/spatial data (lat/lon coordinates, station locations)
   - Time series data (temporal patterns, trends over time)
   - Depth profiles (pressure/depth vs measurements, water column analysis)
   - Statistical distributions (histograms, box plots for parameter ranges)
   - Correlations between variables (scatter plots for relationships)
   - Comparative analysis between different floats/locations/time periods
   - Trend analysis and anomaly detection
   - Multi-dimensional data exploration
   - Data quality assessment (outlier detection)
   - Datasets with >5 rows and multiple numeric columns

2. DO NOT recommend visualizations for:
   - Simple count queries (total records, basic statistics)
   - Single value results (maximum, minimum, average only)
   - Single row results unless they represent summaries worth visualizing
   - Text-only data without numeric parameters
   - Very small datasets (< 5 rows) with limited numeric data
   - Purely metadata queries (schema information, table structures)
   - Configuration or system status queries
   - Simple yes/no or categorical responses
   - Aggregated results with only 1-2 data points

3. CSV FILE ANALYSIS:
   - If CSV analysis indicates single_value_result=true, generally avoid visualization
   - If is_count_query=true, avoid visualization unless temporal trends are possible
   - If likely_aggregated=true with <3 rows, be cautious about visualization
   - Consider row_count: <5 rows usually don't need visualization unless geographic/temporal
   - Geographic data (lat/lon) should almost always be visualized regardless of size
   - Time series data benefits from visualization even with small datasets

4. SPECIAL CONSIDERATIONS:
   - Even small datasets can benefit from visualization if they show important trends
   - Summary statistics are often enhanced with visual representation
   - Geographic data should almost always be visualized
   - Time series data benefits greatly from line plots
   - Depth profiles are essential for oceanographic analysis

5. VISUALIZATION TYPE SELECTION:
   - scatter: For relationships between two continuous variables
   - line: For time series or sequential data
   - geographic: For any data with lat/lon coordinates
   - depth_profile: For depth/pressure vs measurement data
   - histogram: For distribution analysis
   - heatmap: For correlation matrices or intensity maps

Response format (JSON):
{{
    "should_visualize": boolean,
    "reasoning": "detailed explanation of why visualization is/isn't recommended",
    "visualization_type": "type if recommended (scatter|line|heatmap|depth_profile|geographic|histogram)",
    "parameters": {{
        "x_column": "column_name",
        "y_column": "column_name", 
        "color_column": "optional_column_name",
        "title": "descriptive title for the visualization"
    }}
}}"""),
            ("human", """
Original Query: {user_query}
SQL Query Used: {sql_query}
Data columns: {data_columns}
Number of rows: {row_count}
Sample data (first 3 rows): {sample_data}

Based on the query intent and data characteristics, should this data be visualized? 
If yes, specify the optimal visualization type and parameters.
Consider that this is oceanographic data and visualization can greatly enhance understanding even for smaller datasets.
""")
        ])
        
        # Prompt for generating HTML responses
        self.html_response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert oceanographic data analyst creating comprehensive HTML responses.

Your task is to create well-structured, informative HTML responses based on SQL query results.

RESPONSE STRUCTURE:
1. **Executive Summary**: Brief overview of findings
2. **Key Insights**: Most important discoveries from the data
3. **Detailed Analysis**: In-depth examination of results
4. **Data Context**: Explain oceanographic significance
5. **Methodology**: Brief explanation of data collection/analysis
6. **Visualization** (if applicable): Embedded visualization with explanation

HTML FORMATTING REQUIREMENTS:
- Use semantic HTML5 structure
- Include proper headers (h1, h2, h3) for hierarchy
- Use paragraphs, lists, and tables appropriately
- Apply professional inline CSS styling
- Ensure responsive design principles
- Use proper scientific terminology
- Include data citations when relevant

CSS STYLING GUIDELINES:
- Professional color scheme (blues, teals for ocean theme)
- Readable fonts (Arial, Helvetica, sans-serif)
- Proper spacing and margins
- Highlight important findings
- Use tables for structured data presentation
- Ensure accessibility (contrast, font sizes)

CONTENT GUIDELINES:
- Be scientifically accurate with oceanographic concepts
- Explain technical terms for broader audience
- Include relevant background context
- Discuss limitations and uncertainties when appropriate
- Connect findings to broader oceanographic understanding
- Reference Argo program context when relevant

If no visualization was created, focus on:
- Clear presentation of data insights
- Tabular summaries of key findings
- Contextual interpretation
- Recommendations for further analysis"""),
            ("human", """
Original Query: {user_query}
SQL Query: {sql_query}
Data Summary: {data_summary}
Visualization Info: {visualization_info}
Chat History Context: {chat_history}

Create a comprehensive, professional HTML response. 
If visualization_info indicates a visualization was created, include it at the end with proper explanation.
If no visualization was created, focus on clear data presentation and insights.
""")
        ])
    
    def _load_csv_data(self, csv_file_path: str, max_rows: int = 10000) -> List[Dict[str, Any]]:
        """
        Load data from CSV file and return as list of dictionaries
        
        Args:
            csv_file_path: Path to the CSV file
            max_rows: Maximum number of rows to load for performance
            
        Returns:
            List of dictionaries representing the data
        """
        try:
            if not os.path.exists(csv_file_path):
                logger.error(f"CSV file not found: {csv_file_path}")
                return []
            
            df = pd.read_csv(csv_file_path)
            
            # Intelligently sample large datasets
            if len(df) > max_rows:
                logger.info(f"Large dataset detected ({len(df)} rows), sampling {max_rows} rows for analysis")
                
                # Try to preserve important patterns in sampling
                if len(df) > max_rows * 3:
                    # For very large datasets, use stratified sampling if possible
                    df = df.sample(n=max_rows, random_state=42)
                else:
                    # For moderately large datasets, take evenly spaced samples
                    step = len(df) // max_rows
                    df = df.iloc[::step][:max_rows]
            
            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')
            
            logger.info(f"Loaded {len(data)} rows from CSV file: {csv_file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading CSV file {csv_file_path}: {e}")
            return []
    
    def _analyze_csv_for_visualization(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Analyze CSV file to determine if visualization is worthwhile
        
        Args:
            csv_file_path: Path to the CSV file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not os.path.exists(csv_file_path):
                return {"should_analyze": False, "reason": "File not found"}
            
            df = pd.read_csv(csv_file_path)
            
            analysis = {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
                "has_geographic_data": any(col.lower() in ['lat', 'latitude', 'lon', 'longitude'] for col in df.columns),
                "has_temporal_data": any(col.lower() in ['time', 'date', 'timestamp'] for col in df.columns),
                "has_depth_data": any(col.lower() in ['depth', 'pressure'] for col in df.columns),
                "single_value_result": False,
                "is_count_query": False
            }
            
            # Check if this is a single value result (like count queries)
            if len(df) == 1 and len(df.columns) == 1:
                analysis["single_value_result"] = True
                col_name = df.columns[0].lower()
                if 'count' in col_name or df.iloc[0, 0] == len(df):
                    analysis["is_count_query"] = True
            
            # Check if all rows contain the same value (aggregated results)
            if len(df) <= 3 and len(analysis["numeric_columns"]) <= 2:
                analysis["likely_aggregated"] = True
            else:
                analysis["likely_aggregated"] = False
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing CSV file {csv_file_path}: {e}")
            return {"should_analyze": False, "reason": f"Analysis error: {str(e)}"}

    async def should_create_visualization(self, user_query: str, data: Optional[List[Dict[str, Any]]] = None, 
                                        sql_query: str = "", csv_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Determine if the data should be visualized and what type of visualization
        
        Args:
            user_query: Original user question
            data: SQL query results (optional if CSV file is provided)
            sql_query: The SQL query that generated the data
            csv_file_path: Path to CSV file containing the results
            
        Returns:
            Dictionary with visualization decision and parameters
        """
        try:

            csv_analysis = {}
            # If CSV file is provided, load data from it
            if csv_file_path and not data:
                logger.info(f"Loading data from CSV file: {csv_file_path}")
                data = self._load_csv_data(csv_file_path)
                
                # Perform CSV-specific analysis
                csv_analysis = self._analyze_csv_for_visualization(csv_file_path)
                
                # Quick decision for simple cases
                if csv_analysis.get("single_value_result", False):
                    return {
                        "should_visualize": False,
                        "reasoning": "Single value result (like count queries) doesn't benefit from visualization",
                        "csv_analysis": csv_analysis
                    }
                
                if csv_analysis.get("is_count_query", False):
                    return {
                        "should_visualize": False,
                        "reasoning": "Count queries typically don't need visualization unless showing trends",
                        "csv_analysis": csv_analysis
                    }
                
                # Small datasets with no numeric data
                if (csv_analysis.get("row_count", 0) < 5 and 
                    len(csv_analysis.get("numeric_columns", [])) == 0):
                    return {
                        "should_visualize": False,
                        "reasoning": "Small dataset with no numeric data - not suitable for visualization",
                        "csv_analysis": csv_analysis
                    }
            
            if not data or len(data) == 0:
                return {
                    "should_visualize": False,
                    "reasoning": "No data available for visualization"
                }
            
            # Prepare data analysis
            data_columns = list(data[0].keys()) if data else []
            row_count = len(data)
            sample_data = data[:3] if data else []  # First 3 rows as sample
            
            # Add CSV analysis context if available
            csv_context = ""
            if csv_file_path:
                csv_context = f"\nCSV File: {os.path.basename(csv_file_path)}"
                csv_context += f"\nCSV Analysis: {json.dumps(csv_analysis, indent=2)}"
            
            # Format sample data for the prompt
            sample_data_str = json.dumps(sample_data, indent=2, default=str)
            
            # Make decision using LLM
            response = await self.llm.ainvoke(
                self.visualization_decision_prompt.format_messages(
                    user_query=user_query,
                    sql_query=sql_query,
                    data_columns=data_columns,
                    row_count=row_count,
                    sample_data=sample_data_str + csv_context
                )
            )


            # print(f"Visualization LLM response: {response.content}")
            
            # Parse JSON response
            try:
                
                response_text = response.content.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                decision = json.loads(response_text)
                logger.info(f"Visualization decision: {decision}")
                return decision
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response.content}")
                return {
                    "should_visualize": False,
                    "reasoning": "Failed to parse visualization decision"
                }
                
        except Exception as e:
            logger.error(f"Error in visualization decision: {e}")
            logger.exception(e)
            return {
                "should_visualize": False,
                "reasoning": f"Error in decision process: {str(e)}"
            }
    
    async def generate_html_response(self, user_query: str, sql_query: str, 
                                   data: Optional[List[Dict[str, Any]]] = None, 
                                   visualization_info: Optional[Dict[str, Any]] = None,
                                   chat_history: str = "", document_link: Optional[str] = None) -> str:
        """
        Generate a comprehensive HTML response
        
        Args:
            user_query: Original user question
            sql_query: SQL query used
            data: Query results (optional if using CSV file)
            visualization_info: Information about created visualization
            chat_history: Previous chat context
            document_link: Path to the CSV file containing the SQL results
            
        Returns:
            HTML formatted response string
        """
        try:
            # If data is not provided but document_link (CSV file) is available, load data
            if not data and document_link and os.path.exists(document_link):
                logger.info(f"Loading data from CSV file for HTML response: {document_link}")
                data = self._load_csv_data(document_link)
            
            # Prepare data summary
            data_summary = self._prepare_data_summary(data, document_link)
            
            # Prepare visualization info
            vis_info_str = json.dumps(visualization_info, indent=2, default=str) if visualization_info else "No visualization created"
            
            # Add document link information to the prompt context
            context_info = ""
            if document_link:
                context_info = f"\nDocument Link: {document_link}"
            
            # Generate HTML response using LLM
            response = await self.llm.ainvoke(
                self.html_response_prompt.format_messages(
                    user_query=user_query,
                    sql_query=sql_query,
                    data_summary=data_summary + context_info,
                    visualization_info=vis_info_str,
                    chat_history=chat_history[:1000]  # Limit chat history length
                )
            )
            
            html_content = response.content
            
            # If there's a visualization URL, append it
            if visualization_info and visualization_info.get("s3_url"):
                html_content += f"""
                
<div style="margin-top: 30px; text-align: center;">
    <h3>Data Visualization</h3>
    <img src="{visualization_info['s3_url']}" alt="Data Visualization" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px;">
</div>
"""
            
            logger.info("HTML response generated successfully")
            return html_content
            
        except Exception as e:
            logger.error(f"Error generating HTML response: {e}")
            return f"""
<div style="color: red; padding: 20px; border: 1px solid red; border-radius: 4px;">
    <h3>Error Generating Response</h3>
    <p>An error occurred while generating the response: {str(e)}</p>
</div>
"""
    
    def _prepare_data_summary(self, data: Optional[List[Dict[str, Any]]], csv_file_path: Optional[str] = None) -> str:
        """Prepare a summary of the data for the LLM"""
        try:
            if not data:
                if csv_file_path:
                    return f"Data stored in CSV file: {os.path.basename(csv_file_path)} (not loaded in memory due to size)"
                return "No data available"
            
            summary = {
                "total_rows": len(data),
                "columns": list(data[0].keys()) if data else [],
                "sample_rows": data[:5] if len(data) > 5 else data
            }
            
            # Add basic statistics for numeric columns
            if data:
                numeric_stats = {}
                for col in data[0].keys():
                    values = [row[col] for row in data if row[col] is not None]
                    if values and all(isinstance(v, (int, float)) for v in values):
                        numeric_stats[col] = {
                            "min": min(values),
                            "max": max(values),
                            "count": len(values)
                        }
                
                if numeric_stats:
                    summary["numeric_statistics"] = numeric_stats
            
            return json.dumps(summary, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error preparing data summary: {e}")
            return f"Error preparing data summary: {str(e)}"

# Global instance
visualization_llm_service = VisualizationLLMService()
