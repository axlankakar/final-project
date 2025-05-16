# Real-Time Stock Market Data Processing Pipeline

## Overview
This project implements a real-time stock market data processing pipeline that:
- Generates simulated stock market data
- Streams data through Kafka
- Processes data using Spark
- Stores results in PostgreSQL
- Visualizes trends in a dashboard
- Orchestrates the pipeline using Airflow

## Architecture
![Architecture](architecture.png)

### Components
1. **Data Generator**
   - Simulates real-time stock data for multiple companies
   - Generates price, volume, and timestamp data
   - Implements realistic price movements using random walk

2. **Apache Kafka**
   - Handles real-time data streaming
   - Ensures reliable data delivery
   - Provides scalable message queuing

3. **Apache Spark**
   - Processes streaming data in real-time
   - Calculates technical indicators (Moving Averages, RSI)
   - Detects price anomalies and trends

4. **PostgreSQL**
   - Stores processed market data
   - Maintains historical price records
   - Supports dashboard queries

5. **Dashboard**
   - Real-time price charts
   - Technical indicators visualization
   - Price alerts and notifications

6. **Apache Airflow**
   - Orchestrates the entire pipeline
   - Monitors component health
   - Handles error recovery

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- 8GB RAM minimum
- 20GB free disk space

### Quick Start
1. Clone the repository
```bash
git clone <repository-url>
cd stock-market-pipeline
```

2. Start the services
```bash
docker-compose up -d
```

3. Access the interfaces
- Airflow UI: http://localhost:8081 (admin/admin)
- Dashboard: http://localhost:8060
- Spark UI: http://localhost:8089

### Configuration
Key configurations can be modified in:
- `.env` file for environment variables
- `docker-compose.yml` for service settings
- Individual component config files in their respective directories

## Development

### Project Structure
```
.
├── airflow/
│   └── dags/
│       └── stock_pipeline_dag.py
├── data_generator/
│   ├── stock_generator.py
│   └── requirements.txt
├── spark/
│   └── stock_processor.py
├── sql/
│   └── init.sql
├── dashboard/
│   ├── app.py
│   └── requirements.txt
├── docker/
│   ├── data_generator.Dockerfile
│   └── dashboard.Dockerfile
├── .env
├── docker-compose.yml
└── README.md
```

### Adding New Features
1. Stock Symbols: Edit `data_generator/config.py`
2. Technical Indicators: Modify `spark/stock_processor.py`
3. Dashboard Views: Update `dashboard/app.py`

## Monitoring

### Health Checks
- All services have configured health checks
- View status: `docker-compose ps`
- Check logs: `docker-compose logs [service]`

### Common Issues
1. **Services fail to start**
   - Verify port availability
   - Check Docker resources
   - Review service logs

2. **Data not flowing**
   - Confirm Kafka connectivity
   - Check topic creation
   - Verify Spark processing

## License
MIT

## Acknowledgments
Created as part of Data Engineering course project. 