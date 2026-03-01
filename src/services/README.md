# External Services Integration

This directory contains integrations with external APIs and services.

## AGMARKNET Service

The `agmarknet_service.py` module integrates with the Indian government's AGMARKNET portal through the data.gov.in API to fetch real-time mandi (agricultural market) prices.

### API Details

- **API Provider**: Government of India - data.gov.in
- **Data Source**: AGMARKNET Portal (http://agmarknet.gov.in)
- **Endpoint**: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Format**: JSON
- **Authentication**: Optional API key (public access available)

### Features

1. **Real-time Price Fetching**: Retrieves current mandi prices for agricultural commodities
2. **Commodity Mapping**: Maps common crop names to AGMARKNET commodity names
3. **Error Handling**: Graceful fallback to mock data when API is unavailable
4. **Flexible Filtering**: Supports filtering by commodity, state, and district

### Usage

```python
from src.services.agmarknet_service import AgmarknetService

# Initialize service
service = AgmarknetService(api_key='your-api-key')  # API key is optional

# Fetch prices
prices = service.fetch_prices(
    commodity='Wheat',
    state='Maharashtra',
    district='Pune',
    limit=100
)

# Process results
for price in prices:
    print(f"{price.market}: Rs. {price.modal_price}/quintal")
```

### Data Structure

The service returns `AgmarknetPrice` objects with the following fields:

- `state`: State where mandi is located
- `district`: District where mandi is located
- `market`: Name of the mandi/market
- `commodity`: Commodity name
- `variety`: Variety of the commodity
- `arrival_date`: Date of the price
- `min_price`: Minimum price per quintal (Rs.)
- `max_price`: Maximum price per quintal (Rs.)
- `modal_price`: Modal (most common) price per quintal (Rs.)

### Commodity Mapping

The service includes a mapping of common crop names to AGMARKNET commodity names:

| Common Name | AGMARKNET Name |
|-------------|----------------|
| wheat | Wheat |
| rice | Rice |
| paddy | Paddy(Dhan)(Common) |
| soybean | Soyabean |
| cotton | Cotton |
| maize | Maize |
| bajra | Bajra(Pearl Millet/Cumbu) |
| jowar | Jowar(Sorghum) |
| groundnut | Groundnut |
| mustard | Mustard |
| onion | Onion |
| potato | Potato |
| tomato | Tomato |

### Error Handling

The service handles various error scenarios:

1. **API Unavailable**: Falls back to mock data
2. **No Records Found**: Returns empty list
3. **Invalid Records**: Skips malformed records and logs warnings
4. **Network Errors**: Raises `requests.RequestException`

### Configuration

Environment variables:

- `AGMARKNET_API_KEY`: Optional API key for data.gov.in

### Testing

Unit tests are available in `tests/unit/test_agmarknet_service.py`:

```bash
pytest tests/unit/test_agmarknet_service.py -v
```

### References

- [Data.gov.in Commodity Prices](https://data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi)
- [AGMARKNET Portal](http://agmarknet.gov.in)
- [Getting Started with AGMARKNET API](https://lynxbee.com/getting-real-time-indian-agricultural-commodity-market-rates-using-agmarknet-api/)

### Future Enhancements

1. **Caching**: Implement Redis caching for frequently accessed prices
2. **Rate Limiting**: Add rate limiting to respect API quotas
3. **Retry Logic**: Implement exponential backoff for failed requests
4. **More Commodities**: Expand commodity mapping to cover all AGMARKNET commodities
5. **Historical Data**: Add support for fetching historical price trends
6. **Multiple APIs**: Integrate with state-level agricultural marketing board APIs

### Notes

- The API provides wholesale prices (per quintal)
- Prices are updated daily by AGMARKNET
- Modal price is typically used as the representative price
- Some commodities may have multiple varieties with different prices
- Availability varies by state and season
