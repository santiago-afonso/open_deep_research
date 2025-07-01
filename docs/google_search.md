Google Search API#

Overview

The Google Search API provides a programmatic way to retrieve real-time search results using AI. This API enables users to fetch up-to-date information on a given query, making it useful for research, monitoring trends, and accessing the latest insights on various topics.

Technology Stack

FastAPI for API development
Google Search API for retrieving search results
Pydantic for request validation
Azure API Management (APIM) for security and access control
Key Features

Allows users to specify the number of search results to return.
Ensures high relevance by leveraging Google's search capabilities.
Outputs structured JSON responses for easy parsing.
API Usage

Endpoint:

DEV: https://azapimdev.worldbank.org/conversationalai/platform/google_search/
Important Rules

For the Google Search API, kindly ensure that you do not include any World Bank-related OU or higher data classification information in your queries. Please trim the query to exclude such information before passing it on to the API.

Setup

Make sure to check out our Set Up Page

Payload Example

{
  "query": "Latest economic growth trends and GDP forecasts for 2025",
  "num_results": 5
}
Expected Output


[
    {
        "title": "World Economic Outlook - All Issues",
        "link": "https://www.imf.org/en/Publications/WEO",
        "snippet": "Description: Global growth is projected to stay at 3.1 percent in 2024 and rise to 3.2 percent in 2025. Elevated central bank rates to fight inflation and a ..."
    },
    {
        "title": "The Budget and Economic Outlook: 2025 to 2035 | Congressional ...",
        "link": "https://www.cbo.gov/publication/60870",
        "snippet": "Jan 17, 2025 ... In CBO's projections, the federal budget deficit is $1.9 trillion this year, and federal debt rises to 118 percent of GDP in 2035. Economic ..."
    },
    {
        "title": "World Economic Outlook Update, January 2025: Global Growth ...",
        "link": "https://www.imf.org/en/Publications/WEO/Issues/2025/01/17/world-economic-outlook-update-january-2025",
        "snippet": "Jan 17, 2025 ... Global Growth: Divergent and Uncertain. January 2025. Overview; Projections Table; Data Tools; Videos."
    },
    {
        "title": "Our investment and economic outlook, January 2025 | Vanguard",
        "link": "https://corporate.vanguard.com/content/corporatesite/us/en/corp/articles/investment-economic-outlook-jan-2025.html",
        "snippet": "Jan 24, 2025 ... GDP: The economy grew at an annual rate of 3.1% in the third quarter. We foresee 2025 GDP growth remaining above 2%, a view that accounts for ..."
    },
    {
        "title": "Economic Forecast for the US Economy",
        "link": "https://www.conference-board.org/research/us-forecast",
        "snippet": "The unpredictability of the current administration's policies looms large over the outlook. While the US economy is set to start 2025 on strong footing ..."
    }
]
cURL Example

curl -X POST "https://azapim.worldbank.org/conversationalai/platform/google_search/"
     -H "Content-Type: application/json"
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
     -H "Ocp-Apim-Subscription-Key: YOUR_SUBSCRIPTION_KEY" 
     -d '{
  "query": "Latest economic growth trends and GDP forecasts for 2025",
  "num_results": 3
}'
Parameters

query (string): The search query to be executed.
num_results (integer): The number of results to return. The default is 3, but users can specify a different number as needed.