import pandas as pd

def generate_sales_insights(merchant_id, transaction_df):
    """Generate comprehensive sales insights for a specific merchant"""
    merchant_txns = transaction_df[transaction_df['merchant_id'] == merchant_id]

    if merchant_txns.empty:
        return {"error": "No transaction data available for this merchant"}

    # Daily sales trends with more metrics
    daily_sales = merchant_txns.groupby('day_of_week')['order_value'].agg(['sum', 'count', 'mean']).reset_index()
    daily_sales.columns = ['day_of_week', 'total_sales', 'order_count', 'avg_order_value']

    # Create order for days of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_sales['day_order'] = daily_sales['day_of_week'].apply(lambda x: day_order.index(x) if x in day_order else -1)
    daily_sales = daily_sales.sort_values('day_order')

    # Hourly sales trends with more metrics
    hourly_sales = merchant_txns.groupby('hour_of_day')['order_value'].agg(['sum', 'count', 'mean']).reset_index()
    hourly_sales.columns = ['hour_of_day', 'total_sales', 'order_count', 'avg_order_value']
    hourly_sales = hourly_sales.sort_values('hour_of_day')

    # Find peak business hours
    peak_hours = hourly_sales.sort_values('order_count', ascending=False).head(3)

    # Find best-performing days
    best_days = daily_sales.sort_values('total_sales', ascending=False).head(3)

    # Month-over-month growth with growth rate calculation
    monthly_sales = merchant_txns.groupby(['year', 'month'])['order_value'].agg(['sum', 'count']).reset_index()
    monthly_sales.columns = ['year', 'month', 'total_sales', 'order_count']

    # Calculate growth rates when possible
    if len(monthly_sales) > 1:
        monthly_sales = monthly_sales.sort_values(['year', 'month'])
        monthly_sales['prev_sales'] = monthly_sales['total_sales'].shift(1)
        monthly_sales['growth_rate'] = (monthly_sales['total_sales'] - monthly_sales['prev_sales']) / monthly_sales['prev_sales'] * 100

    # Recent performance analysis
    latest_date = merchant_txns['order_time'].max()

    # Last 7 days
    last_7_days = merchant_txns[merchant_txns['order_time'] >= (latest_date - pd.Timedelta(days=7))]
    last_7_days_sales = last_7_days['order_value'].sum() if not last_7_days.empty else 0
    last_7_days_orders = len(last_7_days) if not last_7_days.empty else 0

    # Last 30 days
    last_30_days = merchant_txns[merchant_txns['order_time'] >= (latest_date - pd.Timedelta(days=30))]
    last_30_days_sales = last_30_days['order_value'].sum() if not last_30_days.empty else 0
    last_30_days_orders = len(last_30_days) if not last_30_days.empty else 0

    # Previous 30 days (for comparison)
    prev_30_days = merchant_txns[(merchant_txns['order_time'] < (latest_date - pd.Timedelta(days=30))) &
                                 (merchant_txns['order_time'] >= (latest_date - pd.Timedelta(days=60)))]
    prev_30_days_sales = prev_30_days['order_value'].sum() if not prev_30_days.empty else 0

    # Calculate growth rate
    sales_growth_rate = ((last_30_days_sales - prev_30_days_sales) / prev_30_days_sales * 100) if prev_30_days_sales > 0 else None

    # Identify sales trends
    sales_trend = "increasing" if sales_growth_rate and sales_growth_rate > 5 else \
        "decreasing" if sales_growth_rate and sales_growth_rate < -5 else "stable"

    # Sales forecast (simple linear projection)
    # Using daily sales data to predict next 7 days
    forecast = [0] * 7  # Default value
    if not merchant_txns.empty:
        merchant_txns = merchant_txns.copy()
        merchant_txns['date'] = merchant_txns['order_time'].dt.date
        daily_totals = merchant_txns.groupby('date')['order_value'].sum().reset_index()
        daily_totals['day_number'] = range(1, len(daily_totals) + 1)

        if len(daily_totals) > 5:  # Need enough data for meaningful projection
            # Simple linear regression
            import numpy as np
            from sklearn.linear_model import LinearRegression

            x = np.array(daily_totals['day_number']).reshape(-1, 1)
            y = np.array(daily_totals['order_value'])

            model = LinearRegression().fit(x, y)

            # Predict next 7 days
            next_days = np.array(range(len(daily_totals) + 1, len(daily_totals) + 8)).reshape(-1, 1)
            forecast = model.predict(next_days)

            # Ensure no negative forecasts
            forecast = np.maximum(forecast, 0)
        else:
            # Not enough data, use average
            forecast = [daily_totals['order_value'].mean()] * 7

    # Wait time analysis
    wait_time_stats = merchant_txns['wait_time'].describe().to_dict()

    return {
        'daily_trends': daily_sales,
        'hourly_trends': hourly_sales,
        'peak_hours': peak_hours,
        'best_days': best_days,
        'monthly_sales': monthly_sales,
        'last_7_days_sales': last_7_days_sales,
        'last_7_days_orders': last_7_days_orders,
        'last_30_days_sales': last_30_days_sales,
        'last_30_days_orders': last_30_days_orders,
        'prev_30_days_sales': prev_30_days_sales,
        'sales_growth_rate': sales_growth_rate,
        'sales_trend': sales_trend,
        'sales_forecast': list(forecast) if isinstance(forecast, np.ndarray) else forecast,
        'wait_time_stats': wait_time_stats,
        'recent_performance': last_30_days_sales  # Kept for backward compatibility
    }

def generate_inventory_insights(merchant_id, transaction_item_df, items_df):
    """Generate comprehensive inventory insights for a specific merchant"""
    try:
        # Get all items from this merchant
        merchant_items = items_df[items_df['merchant_id'] == merchant_id]

        if merchant_items.empty:
            return {
                'inventory_status': 'Inventory status not available.',
                'error': "No inventory data available for this merchant"
            }

        # Get item order counts
        item_orders = transaction_item_df[transaction_item_df['merchant_id'] == merchant_id]

        if item_orders.empty:
            return {
                'inventory_status': 'Inventory status not available.',
                'total_items': len(merchant_items),
                'active_items': 0,
                'error': "No transaction data available for inventory analysis"
            }

        item_counts = item_orders.groupby('item_id').size().reset_index(name='order_count')

        # Merge with item details
        item_performance = item_counts.merge(merchant_items, on='item_id')

        # If no performance data was calculated, return appropriate status
        if item_performance.empty:
            return {
                'inventory_status': 'Inventory status not available.',
                'error': "No performance data available for items"
            }

        # Calculate revenue per item
        item_performance['revenue'] = item_performance['item_price'] * item_performance['order_count']

        # Calculate profit margins
        item_performance['estimated_cost'] = item_performance['item_price'] * 0.6  # Assuming 40% margin
        item_performance['profit'] = item_performance['revenue'] - (item_performance['estimated_cost'] * item_performance['order_count'])
        item_performance['profit_margin'] = (item_performance['profit'] / item_performance['revenue']) * 100

        # Find various performance metrics
        top_sellers = item_performance.sort_values('order_count', ascending=False).head(5)
        slow_movers = item_performance.sort_values('order_count').head(5)
        profitable_items = item_performance.sort_values('profit', ascending=False).head(5)
        high_margin_items = item_performance.sort_values('profit_margin', ascending=False).head(5)

        # Item pairings analysis - what items are commonly ordered together
        order_items = item_orders.groupby('order_id')['item_id'].apply(list).reset_index()
        item_pairs = {}

        # Process each order to count pairs
        for _, row in order_items.iterrows():
            items = row['item_id']
            if len(items) > 1:
                for i, item1 in enumerate(items):
                    for item2 in items[i+1:]:
                        pair = tuple(sorted([item1, item2]))
                        if pair in item_pairs:
                            item_pairs[pair] += 1
                        else:
                            item_pairs[pair] = 1

        # Convert to DataFrame
        common_pairs = None
        if item_pairs:
            import pandas as pd
            pairs_df = pd.DataFrame([
                {'item1': p[0], 'item2': p[1], 'count': c}
                for p, c in item_pairs.items()
            ])

            # Add item names
            item_names = merchant_items[['item_id', 'item_name']].set_index('item_id')['item_name'].to_dict()

            if not pairs_df.empty:
                pairs_df['item1_name'] = pairs_df['item1'].map(item_names)
                pairs_df['item2_name'] = pairs_df['item2'].map(item_names)
                common_pairs = pairs_df.sort_values('count', ascending=False).head(5)

        # Price point analysis
        price_distribution = merchant_items['item_price'].describe().to_dict()

        # Return the insights including inventory status
        return {
            'inventory_status': 'Inventory insights available.',
            'top_sellers': top_sellers,
            'slow_movers': slow_movers,
            'profitable_items': profitable_items,  # Now based on profit, not revenue
            'high_margin_items': high_margin_items,
            'item_performance': item_performance,  # Complete dataset with all metrics
            'common_pairs': common_pairs,
            'price_distribution': price_distribution,
            'total_items': len(merchant_items),
            'active_items': len(item_performance)
        }
    except Exception as e:
        return {
            'inventory_status': 'Inventory status not available.',
            'error': f"An error occurred while generating inventory insights: {str(e)}"
        }


def generate_customer_insights(merchant_id, transaction_df):
    """Generate comprehensive customer insights for a specific merchant"""
    # Ensure transaction_df has wait_time calculated before passing to this function
    # transaction_df should have wait_time = (delivery_time - order_time).dt.total_seconds() / 60

    merchant_txns = transaction_df[transaction_df['merchant_id'] == merchant_id]

    if merchant_txns.empty:
        return {"error": "No transaction data available for customer analysis"}

    # Customer stats and segmentation analysis
    customer_stats = merchant_txns.groupby('eater_id').agg({
        'order_id': 'count',  # Order frequency
        'order_value': ['sum', 'mean', 'median'],  # Spending patterns
        'order_time': ['min', 'max'],  # First and last order
        'wait_time': 'mean'  # Average wait time
    })

    # Flatten multi-level column index
    customer_stats.columns = ['_'.join(col).strip() for col in customer_stats.columns.values]
    customer_stats = customer_stats.reset_index()

    # Rename columns for clarity
    customer_stats.rename(columns={
        'order_id_count': 'order_count',
        'order_value_sum': 'total_spent',
        'order_value_mean': 'avg_order_value',
        'order_value_median': 'median_order_value',
        'order_time_min': 'first_order',
        'order_time_max': 'last_order',
        'wait_time_mean': 'avg_wait_time'
    }, inplace=True)

    # Calculate days since first and last order
    latest_date = merchant_txns['order_time'].max()
    customer_stats['days_since_first_order'] = (latest_date - customer_stats['first_order']).dt.days
    customer_stats['days_since_last_order'] = (latest_date - customer_stats['last_order']).dt.days

    # Calculate customer lifetime
    customer_stats['customer_lifetime_days'] = (customer_stats['last_order'] - customer_stats['first_order']).dt.days

    # The repeat customer logic is correct
    customer_stats['customer_type'] = customer_stats['order_count'].apply(
        lambda x: 'repeat' if x > 1 else 'one-time')

    repeat_customers = customer_stats[customer_stats['order_count'] > 1]
    total_customers = len(customer_stats)
    repeat_rate = len(repeat_customers) / total_customers if total_customers > 0 else 0

    # Rest of function remains the same...

    # Calculate recency, frequency, monetary (RFM) scores
    if not customer_stats.empty:
        import pandas as pd

        # Recency score (lower days_since_last_order is better)
        try:
            customer_stats['recency_score'] = pd.qcut(
                customer_stats['days_since_last_order'],
                q=5,
                labels=[5, 4, 3, 2, 1],
                duplicates='drop'
            )
        except ValueError:
            customer_stats['recency_score'] = 3  # Default if not enough unique values

        # Frequency score (higher order_count is better)
        try:
            customer_stats['frequency_score'] = pd.qcut(
                customer_stats['order_count'],
                q=5,
                labels=[1, 2, 3, 4, 5],
                duplicates='drop'
            )
        except ValueError:
            customer_stats['frequency_score'] = 3

        # Monetary score (higher total_spent is better)
        try:
            customer_stats['monetary_score'] = pd.qcut(
                customer_stats['total_spent'],
                q=5,
                labels=[1, 2, 3, 4, 5],
                duplicates='drop'
            )
        except ValueError:
            customer_stats['monetary_score'] = 3

        # Calculate overall RFM score
        customer_stats['rfm_score'] = customer_stats['recency_score'].astype(int) + \
                                      customer_stats['frequency_score'].astype(int) + \
                                      customer_stats['monetary_score'].astype(int)

        # Customer segmentation based on RFM
        try:
            customer_stats['segment'] = pd.qcut(
                customer_stats['rfm_score'],
                q=4,
                labels=['Low-Value', 'Medium-Value', 'High-Value', 'Top'],
                duplicates='drop'
            )
        except ValueError:
            # Simple segmentation based on total spent
            try:
                customer_stats['segment'] = pd.qcut(
                    customer_stats['total_spent'],
                    q=4,
                    labels=['Low-Value', 'Medium-Value', 'High-Value', 'Top'],
                    duplicates='drop'
                )
            except ValueError:
                # Manual segmentation as fallback
                def assign_segment(row):
                    if row['order_count'] >= 3 and row['total_spent'] > customer_stats['total_spent'].median():
                        return 'Top'
                    elif row['order_count'] >= 2:
                        return 'High-Value'
                    elif row['total_spent'] > customer_stats['total_spent'].median():
                        return 'Medium-Value'
                    else:
                        return 'Low-Value'

                customer_stats['segment'] = customer_stats.apply(assign_segment, axis=1)

        # Get segment distribution
        segment_distribution = customer_stats['segment'].value_counts().to_dict()

        # Identify top customers
        high_value_customers = customer_stats.sort_values('total_spent', ascending=False).head(10)

        # Customer acquisition trend
        customer_acquisition = merchant_txns.drop_duplicates('eater_id')[['eater_id', 'order_time']]
        customer_acquisition['acquisition_month'] = customer_acquisition['order_time'].dt.to_period('M')
        new_customers_by_month = customer_acquisition.groupby('acquisition_month').size().reset_index(name='new_customers')

        # Average order value trend
        aov_trend = merchant_txns.copy()
        aov_trend['month'] = aov_trend['order_time'].dt.to_period('M')
        aov_by_month = aov_trend.groupby('month')['order_value'].mean().reset_index(name='avg_order_value')

        # Customer retention analysis
        # Identify cohorts based on first order month
        cohort_data = customer_acquisition.copy()
        cohort_data['cohort'] = cohort_data['order_time'].dt.to_period('M')

        # Get all orders with cohort information
        cohort_orders = merchant_txns.merge(
            cohort_data[['eater_id', 'cohort']],
            on='eater_id',
            how='left'
        )

        # Calculate retention rates by cohort
        cohort_orders['order_month'] = cohort_orders['order_time'].dt.to_period('M')
        cohort_orders['months_since_first_order'] = (cohort_orders['order_month'] - cohort_orders['cohort']).apply(lambda x: x.n)

        # Count distinct customers by cohort and month
        cohort_retention = cohort_orders.groupby(['cohort', 'months_since_first_order'])['eater_id'].nunique().reset_index()

        # Calculate initial cohort sizes
        cohort_sizes = cohort_orders.groupby('cohort')['eater_id'].nunique().reset_index(name='cohort_size')

        # Merge to get retention rates
        cohort_retention = cohort_retention.merge(cohort_sizes, on='cohort')
        cohort_retention['retention_rate'] = cohort_retention['eater_id'] / cohort_retention['cohort_size']

        return {
            'customer_stats': customer_stats,
            'total_customers': total_customers,
            'repeat_customers': len(repeat_customers),
            'repeat_customer_percentage': repeat_rate * 100,
            'high_value_customers': high_value_customers,
            'segment_distribution': segment_distribution,
            'new_customers_by_month': new_customers_by_month,
            'aov_by_month': aov_by_month,
            'cohort_retention': cohort_retention,
            'overall_retention': repeat_rate,
            'delivery_time_by_customer': customer_stats[['eater_id', 'avg_wait_time']]
        }
    else:
        return {
            'total_customers': 0,
            'repeat_customers': 0,
            'repeat_customer_percentage': 0,
            'error': "Insufficient data for customer segmentation"
        }

def generate_benchmark_insights(merchant_id, merchant_df, transaction_df, items_df):
    """Generate insights by comparing merchant performance against peers in the same cuisine category.
    Returns detailed analysis of relative performance across key metrics."""
    # Get merchant category
    merchant_info = items_df[items_df['merchant_id'] == merchant_id]
    if merchant_info.empty:
        return {"error": "Merchant not found"}

    # Check if the merchant_df has a 'cuisine_tag' column
    merchant_category = None
    if 'cuisine_tag' in items_df.columns:
        merchant_category = merchant_info['cuisine_tag'].iloc[0]
        peer_merchants = items_df[items_df['cuisine_tag'] == merchant_category]
        category_name = merchant_category
    else:
        peer_merchants = items_df
        category_name = "all merchants"

    peer_ids = list(peer_merchants['merchant_id'])
    if not peer_ids or len(peer_ids) <= 1:
        return {"error": "Insufficient peer data for benchmarking"}

    # Remove current merchant from peer list
    peer_ids = [mid for mid in peer_ids if mid != merchant_id]
    if not peer_ids:
        return {"error": "No peers found in the same category"}

    # Get peer transactions and merchant transactions
    peer_txns = transaction_df[transaction_df['merchant_id'].isin(peer_ids)]
    merchant_txns = transaction_df[transaction_df['merchant_id'] == merchant_id]
    if peer_txns.empty or merchant_txns.empty:
        return {"error": "Insufficient transaction data for benchmarking"}

    # Calculate average metrics for peers
    peer_metrics = {}
    insights = {
        "merchant_category": merchant_category,  # Add the merchant's cuisine category
        "summary": f"Performance comparison against {len(peer_ids)} peers in {category_name}",
        "strengths": [],
        "opportunities": [],
        "metrics_detail": {},
        "peer_count": len(peer_ids)
    }

    # Average order value
    peer_aov = peer_txns['order_value'].mean()
    merchant_aov = merchant_txns['order_value'].mean()
    peer_metrics['aov'] = {
        'peer_avg': peer_aov,
        'merchant': merchant_aov,
        'difference': merchant_aov - peer_aov,
        'difference_pct': (merchant_aov - peer_aov) / peer_aov * 100 if peer_aov > 0 else 0
    }

    insights["metrics_detail"]["average_order_value"] = peer_metrics['aov']
    if peer_metrics['aov']['difference_pct'] >= 10:
        insights["strengths"].append(f"Average order value is {abs(round(peer_metrics['aov']['difference_pct']))}% higher than category average")
    elif peer_metrics['aov']['difference_pct'] <= -10:
        insights["opportunities"].append(f"Average order value is {abs(round(peer_metrics['aov']['difference_pct']))}% below category average")

    # Order volume (normalized by time period)
    peer_order_count = len(peer_txns) / len(peer_ids)  # Average orders per peer
    merchant_order_count = len(merchant_txns)
    peer_metrics['order_volume'] = {
        'peer_avg': peer_order_count,
        'merchant': merchant_order_count,
        'difference': merchant_order_count - peer_order_count,
        'difference_pct': (merchant_order_count - peer_order_count) / peer_order_count * 100 if peer_order_count > 0 else 0
    }

    insights["metrics_detail"]["order_volume"] = peer_metrics['order_volume']
    if peer_metrics['order_volume']['difference_pct'] >= 15:
        insights["strengths"].append(f"Order volume is {abs(round(peer_metrics['order_volume']['difference_pct']))}% higher than peers")
    elif peer_metrics['order_volume']['difference_pct'] <= -15:
        insights["opportunities"].append(f"Order volume is {abs(round(peer_metrics['order_volume']['difference_pct']))}% below peers")

    # Wait times
    peer_wait_time = peer_txns['wait_time'].mean()
    merchant_wait_time = merchant_txns['wait_time'].mean()
    peer_metrics['wait_time'] = {
        'peer_avg': peer_wait_time,
        'merchant': merchant_wait_time,
        'difference': merchant_wait_time - peer_wait_time,
        'difference_pct': (merchant_wait_time - peer_wait_time) / peer_wait_time * 100 if peer_wait_time > 0 else 0
    }

    insights["metrics_detail"]["wait_time"] = peer_metrics['wait_time']
    if peer_metrics['wait_time']['difference_pct'] <= -10:
        insights["strengths"].append(f"Wait times are {abs(round(peer_metrics['wait_time']['difference_pct']))}% faster than category average")
    elif peer_metrics['wait_time']['difference_pct'] >= 10:
        insights["opportunities"].append(f"Wait times are {abs(round(peer_metrics['wait_time']['difference_pct']))}% longer than category average")

    # Customer retention
    # Count repeat customers for peers
    peer_customer_counts = peer_txns.groupby(['merchant_id', 'eater_id']).size().reset_index(name='order_count')
    peer_repeat_customers = peer_customer_counts[peer_customer_counts['order_count'] > 1]
    peer_repeat_rate = len(peer_repeat_customers) / len(peer_customer_counts) if len(peer_customer_counts) > 0 else 0

    # Count repeat customers for merchant
    merchant_customer_counts = merchant_txns.groupby('eater_id').size().reset_index(name='order_count')
    merchant_repeat_customers = merchant_customer_counts[merchant_customer_counts['order_count'] > 1]
    merchant_repeat_rate = len(merchant_repeat_customers) / len(merchant_customer_counts) if len(merchant_customer_counts) > 0 else 0

    peer_metrics['repeat_rate'] = {
        'peer_avg': peer_repeat_rate,
        'merchant': merchant_repeat_rate,
        'difference': merchant_repeat_rate - peer_repeat_rate,
        'difference_pct': (merchant_repeat_rate - peer_repeat_rate) / peer_repeat_rate * 100 if peer_repeat_rate > 0 else 0
    }

    insights["metrics_detail"]["customer_retention"] = peer_metrics['repeat_rate']
    if peer_metrics['repeat_rate']['difference_pct'] >= 10:
        insights["strengths"].append(f"Customer retention is {abs(round(peer_metrics['repeat_rate']['difference_pct']))}% higher than peers")
    elif peer_metrics['repeat_rate']['difference_pct'] <= -10:
        insights["opportunities"].append(f"Customer retention is {abs(round(peer_metrics['repeat_rate']['difference_pct']))}% below peers")

    # Menu size comparison
    peer_items = items_df[items_df['merchant_id'].isin(peer_ids)]
    peer_item_counts = peer_items.groupby('merchant_id')['item_id'].count()
    avg_peer_menu_size = peer_item_counts.mean() if not peer_item_counts.empty else 0

    merchant_menu_size = len(items_df[items_df['merchant_id'] == merchant_id])

    peer_metrics['menu_size'] = {
        'peer_avg': avg_peer_menu_size,
        'merchant': merchant_menu_size,
        'difference': merchant_menu_size - avg_peer_menu_size,
        'difference_pct': (merchant_menu_size - avg_peer_menu_size) / avg_peer_menu_size * 100 if avg_peer_menu_size > 0 else 0
    }

    insights["metrics_detail"]["menu_size"] = peer_metrics['menu_size']
    if abs(peer_metrics['menu_size']['difference_pct']) >= 25:
        if peer_metrics['menu_size']['difference_pct'] > 0:
            insights["strengths"].append(f"Menu is {abs(round(peer_metrics['menu_size']['difference_pct']))}% larger than category average")
        else:
            insights["opportunities"].append(f"Menu is {abs(round(peer_metrics['menu_size']['difference_pct']))}% smaller than category average")

    # Price point comparison
    merchant_items = items_df[items_df['merchant_id'] == merchant_id]
    peer_avg_price = peer_items['item_price'].mean() if not peer_items.empty else 0
    merchant_avg_price = merchant_items['item_price'].mean() if not merchant_items.empty else 0

    peer_metrics['price_point'] = {
        'peer_avg': peer_avg_price,
        'merchant': merchant_avg_price,
        'difference': merchant_avg_price - peer_avg_price,
        'difference_pct': (merchant_avg_price - peer_avg_price) / peer_avg_price * 100 if peer_avg_price > 0 else 0
    }

    insights["metrics_detail"]["price_point"] = peer_metrics['price_point']
    if abs(peer_metrics['price_point']['difference_pct']) >= 15:
        comparative = "premium" if peer_metrics['price_point']['difference_pct'] > 0 else "value"
        insights["strengths"].append(f"{comparative.capitalize()} pricing strategy with items {abs(round(peer_metrics['price_point']['difference_pct']))}% {comparative} compared to peers")

    # Overall benchmark score (simple average of all metrics)
    score_metrics = ['aov', 'order_volume', 'repeat_rate']  # Metrics where higher is better
    inverse_metrics = ['wait_time']  # Metrics where lower is better

    # Calculate overall score
    overall_score = 0
    count = 0

    for metric in score_metrics:
        if metric in peer_metrics and peer_metrics[metric]['peer_avg'] > 0:
            ratio = peer_metrics[metric]['merchant'] / peer_metrics[metric]['peer_avg']
            score = min(ratio, 2)  # Cap at 2x benchmark
            overall_score += score
            count += 1

    for metric in inverse_metrics:
        if metric in peer_metrics and peer_metrics[metric]['peer_avg'] > 0 and peer_metrics[metric]['merchant'] > 0:
            ratio = peer_metrics[metric]['peer_avg'] / peer_metrics[metric]['merchant']  # Inverse ratio (lower is better)
            score = min(ratio, 2)  # Cap at 2x benchmark
            overall_score += score
            count += 1

    if count > 0:
        overall_score = overall_score / count
    else:
        overall_score = 1  # Default to average

    insights["overall_score"] = overall_score

    # Add overall performance assessment
    if overall_score >= 1.3:
        insights["performance_tier"] = "Top performer"
        insights["summary"] = f"Top performer among {len(peer_ids)} peers in {category_name}"
    elif overall_score >= 1.1:
        insights["performance_tier"] = "Above average"
        insights["summary"] = f"Above average performance among {len(peer_ids)} peers in {category_name}"
    elif overall_score >= 0.9:
        insights["performance_tier"] = "Average performer"
    elif overall_score >= 0.7:
        insights["performance_tier"] = "Below average"
        insights["summary"] = f"Below average performance among {len(peer_ids)} peers in {category_name}"
    else:
        insights["performance_tier"] = "Underperformer"
        insights["summary"] = f"Underperforming compared to {len(peer_ids)} peers in {category_name}"

    # Add recommendations based on opportunities
    if insights["opportunities"]:
        insights["recommendations"] = []
        if any("order value" in opp for opp in insights["opportunities"]):
            insights["recommendations"].append("Consider bundling or upselling strategies to increase average order value")
        if any("wait time" in opp for opp in insights["opportunities"]):
            insights["recommendations"].append("Review operational efficiency to reduce customer wait times")
        if any("retention" in opp for opp in insights["opportunities"]):
            insights["recommendations"].append("Implement loyalty programs to improve customer retention")
        if any("order volume" in opp for opp in insights["opportunities"]):
            insights["recommendations"].append("Review marketing strategy to increase order volume")

    return insights

def generate_location_insights(merchant_id, merchant_df, transaction_df, items_df, transaction_item_df):
    """Generate insights about the merchant's performance in their city location"""

    # Get merchant's city
    if merchant_df[merchant_df['merchant_id'] == merchant_id].empty:
        return {"error": "Merchant not found"}

    merchant_city_id = merchant_df[merchant_df['merchant_id'] == merchant_id]['city_id'].iloc[0]

    # Find all merchants in the same city
    city_merchants = merchant_df[merchant_df['city_id'] == merchant_city_id]
    city_merchant_ids = city_merchants['merchant_id'].tolist()

    # Get all transactions in this city
    city_transactions = transaction_df[transaction_df['merchant_id'].isin(city_merchant_ids)]

    if city_transactions.empty:
        return {
            "merchant_city_id": merchant_city_id,
            "error": "No transaction data available for this city"
        }

    # City sales overview
    city_sales = city_transactions.groupby('merchant_id')['order_value'].sum().reset_index()
    city_sales = city_sales.merge(merchant_df[['merchant_id']], on='merchant_id')

    # Get the merchant's sales and rank in city
    merchant_sales = city_sales[city_sales['merchant_id'] == merchant_id]['order_value'].iloc[0] if not city_sales[city_sales['merchant_id'] == merchant_id].empty else 0
    city_sales_rank = city_sales[city_sales['order_value'] > merchant_sales].shape[0] + 1

    # Generate city-level item performance
    city_items = transaction_item_df[transaction_item_df['merchant_id'].isin(city_merchant_ids)]
    city_items = city_items.merge(items_df, on=['item_id', 'merchant_id'])

    # City's best selling items (all merchants)
    if not city_items.empty:
        item_popularity = city_items.groupby('item_id').size().reset_index(name='order_count')
        item_popularity = item_popularity.merge(items_df[['item_id', 'item_name']], on='item_id')
        best_city_items = item_popularity.sort_values('order_count', ascending=False).head(5)
        worst_city_items = item_popularity.sort_values('order_count').head(5)
    else:
        best_city_items = pd.DataFrame()
        worst_city_items = pd.DataFrame()

    # Get merchant's items
    merchant_items = items_df[items_df['merchant_id'] == merchant_id]

    # Compare merchant's items to city popularity
    merchant_item_popularity = None
    if not merchant_items.empty and not city_items.empty:
        merchant_transactions = transaction_item_df[transaction_item_df['merchant_id'] == merchant_id]
        if not merchant_transactions.empty:
            merchant_item_counts = merchant_transactions.groupby('item_id').size().reset_index(name='merchant_order_count')
            merchant_item_popularity = merchant_item_counts.merge(merchant_items[['item_id', 'item_name']], on='item_id')

            # Get city average for these items (where available)
            city_item_counts = city_items.groupby('item_id').size().reset_index(name='city_order_count')
            merchant_item_popularity = merchant_item_popularity.merge(city_item_counts, on='item_id', how='left')
            merchant_item_popularity['city_order_count'] = merchant_item_popularity['city_order_count'].fillna(0)

            # Calculate relative popularity
            city_merchant_count = len(city_merchant_ids)
            if city_merchant_count > 0:
                merchant_item_popularity['city_avg_per_merchant'] = merchant_item_popularity['city_order_count'] / city_merchant_count
                merchant_item_popularity['relative_performance'] = merchant_item_popularity['merchant_order_count'] / merchant_item_popularity['city_avg_per_merchant']
                # Replace inf with a large number
                merchant_item_popularity['relative_performance'] = merchant_item_popularity['relative_performance'].replace([float('inf')], 10)
                merchant_item_popularity = merchant_item_popularity.sort_values('relative_performance', ascending=False)

    # Category performance in city
    # Check if 'cuisine_tag' or category exists in the data
    category_column = None
    for col in ['cuisine_tag', 'category', 'merchant_category']:
        if col in items_df.columns:
            category_column = col
            break

    category_performance = None
    if category_column:
        # Get merchant's category
        merchant_category = merchant_items[category_column].iloc[0] if not merchant_items.empty else None

        if merchant_category:
            # Group transactions by merchant category
            city_items_with_cat = city_items.dropna(subset=[category_column])
            if not city_items_with_cat.empty:
                category_sales = city_items_with_cat.groupby(category_column).size().reset_index(name='order_count')
                category_performance = category_sales.sort_values('order_count', ascending=False)

                # Find merchant's category rank
                merchant_category_rank = category_performance[category_performance[category_column] == merchant_category].index[0] + 1 if merchant_category in category_performance[category_column].values else None

    # Find opportunities based on city trends
    opportunities = []
    strengths = []

    # Analyze if merchant offers city's popular items
    if not best_city_items.empty and not merchant_items.empty:
        top_city_items = set(best_city_items['item_name'].head(10))
        merchant_item_names = set(merchant_items['item_name'])
        missing_popular_items = top_city_items - merchant_item_names

        if missing_popular_items:
            opportunities.append(f"Consider adding popular city items: {', '.join(list(missing_popular_items)[:3])}")

    # Check if merchant's items are performing well in the city context
    if merchant_item_popularity is not None:
        outperforming_items = merchant_item_popularity[merchant_item_popularity['relative_performance'] > 1.5]
        if not outperforming_items.empty:
            strengths.append(f"Your top items outperform city averages: {', '.join(outperforming_items['item_name'].head(3))}")

        underperforming_items = merchant_item_popularity[merchant_item_popularity['relative_performance'] < 0.5]
        if not underperforming_items.empty:
            opportunities.append(f"Some items underperform compared to city averages: {', '.join(underperforming_items['item_name'].head(3))}")

    # Category recommendations
    if category_performance is not None and category_column is not None:
        best_categories = category_performance[category_column].head(3).tolist()
        worst_categories = category_performance[category_column].tail(3).tolist()

        if merchant_category and merchant_category not in best_categories:
            opportunities.append(f"Consider adding items from popular categories: {', '.join(best_categories)}")

        if merchant_category and merchant_category in best_categories:
            strengths.append(f"Your category ({merchant_category}) is among the most popular in the city")

    # Customer geographic insights
    # If eater_id can be mapped to locations or zones
    # This would be a placeholder - in a real system, you might have customer location data

    return {
        "merchant_city_id": merchant_city_id,
        "city_merchant_count": len(city_merchant_ids),
        "merchant_sales_rank": city_sales_rank,
        "merchants_in_city": len(city_merchant_ids),
        "best_city_items": best_city_items,
        "worst_city_items": worst_city_items,
        "merchant_item_city_performance": merchant_item_popularity,
        "category_performance": category_performance,
        "opportunities": opportunities,
        "strengths": strengths,
        "relative_sales": {
            "merchant_sales": merchant_sales,
            "city_average": city_sales['order_value'].mean(),
            "city_median": city_sales['order_value'].median(),
            "city_top": city_sales['order_value'].max()
        }
    }

def generate_keyword_insights(merchant_id, transaction_item_df, items_df, keyword_df):
    """Generate insights about search keywords related to the merchant's menu items"""
    # Get merchant's items
    merchant_items = items_df[items_df['merchant_id'] == merchant_id]

    if merchant_items.empty:
        return {"error": "No menu items found for this merchant"}

    # Extract item names and split into individual words
    item_words = set()
    for name in merchant_items['item_name']:
        # Split the item name into words
        words = name.lower().split()
        # Add each word to the set
        for word in words:
            # Clean the word (remove punctuation)
            word = ''.join(e for e in word if e.isalnum())
            if len(word) > 2:  # Only include words with 3+ characters
                item_words.add(word)

    # Filter keywords that are relevant to this merchant
    relevant_keywords = []
    for _, row in keyword_df.iterrows():
        keyword = str(row['keyword']).lower()
        # Check if any word in the keyword matches merchant's items
        keyword_words = keyword.split()

        # If any word in the keyword matches a word in the merchant's items, it's relevant
        if any(word in item_words for word in keyword_words):
            relevant_keywords.append(row)

    # If we have enough relevant keywords, create a DataFrame
    if relevant_keywords:
        relevant_df = pd.DataFrame(relevant_keywords)
    else:
        # Use fuzzy matching as a fallback
        from fuzzywuzzy import process

        # Get all item names as a list
        item_names = merchant_items['item_name'].tolist()

        # Find closest matches for each keyword
        relevant_keywords = []
        for _, row in keyword_df.iterrows():
            keyword = str(row['keyword']).lower()

            # Find the closest matching item name
            matches = process.extractOne(keyword, item_names)
            if matches and matches[1] > 70:  # 70% similarity threshold
                relevant_keywords.append(row)

        if relevant_keywords:
            relevant_df = pd.DataFrame(relevant_keywords)
        else:
            return {
                "error": "No relevant keywords found for this merchant's menu items",
                "suggestion": "Consider adding more descriptive item names to match common search terms"
            }

    # Calculate conversion metrics
    relevant_df['view_to_menu_rate'] = relevant_df['menu'] / relevant_df['view'] * 100
    relevant_df['menu_to_checkout_rate'] = relevant_df['checkout'] / relevant_df['menu'] * 100
    relevant_df['checkout_to_order_rate'] = relevant_df['order'] / relevant_df['checkout'] * 100
    relevant_df['overall_conversion'] = relevant_df['order'] / relevant_df['view'] * 100

    # Add a search popularity score (normalized)
    max_views = keyword_df['view'].max()
    relevant_df['popularity_score'] = (relevant_df['view'] / max_views * 100).round(1)

    # Sort by different metrics for different insights
    top_searched = relevant_df.sort_values('view', ascending=False).head(10)
    best_converting = relevant_df.sort_values('overall_conversion', ascending=False).head(10)
    high_abandonment = relevant_df[relevant_df['view'] > 100].sort_values('overall_conversion').head(10)

    # Use machine learning to cluster keywords if we have enough data
    clusters = None
    if len(relevant_df) >= 20:
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler

            # Select features for clustering
            features = ['view', 'view_to_menu_rate', 'menu_to_checkout_rate', 'checkout_to_order_rate']
            X = relevant_df[features].fillna(0)

            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Determine optimal number of clusters (up to 5)
            from sklearn.metrics import silhouette_score
            best_score = -1
            best_n = 2

            for n in range(2, min(6, len(relevant_df) // 5 + 1)):
                kmeans = KMeans(n_clusters=n, random_state=42)
                labels = kmeans.fit_predict(X_scaled)

                if len(set(labels)) > 1:  # Ensure we have more than one cluster
                    score = silhouette_score(X_scaled, labels)
                    if score > best_score:
                        best_score = score
                        best_n = n

            # Perform clustering with optimal number of clusters
            kmeans = KMeans(n_clusters=best_n, random_state=42)
            relevant_df['cluster'] = kmeans.fit_predict(X_scaled)

            # Get cluster centers and interpret them
            centers = scaler.inverse_transform(kmeans.cluster_centers_)

            clusters = []
            for i in range(best_n):
                cluster_df = relevant_df[relevant_df['cluster'] == i].copy()

                # Determine cluster characteristics
                avg_view = centers[i][0]
                avg_v2m = centers[i][1]
                avg_m2c = centers[i][2]
                avg_c2o = centers[i][3]

                # Name the cluster based on characteristics
                if avg_v2m > 50 and avg_m2c > 30 and avg_c2o > 70:
                    cluster_type = "High-Converting Keywords"
                elif avg_view > relevant_df['view'].mean() * 2:
                    cluster_type = "Popular Search Terms"
                elif avg_v2m < 20 or avg_m2c < 10 or avg_c2o < 30:
                    cluster_type = "Poor-Converting Keywords"
                else:
                    cluster_type = f"Keyword Group {i+1}"

                # Get top keywords in this cluster
                top_cluster_keywords = cluster_df.sort_values('view', ascending=False).head(5)

                clusters.append({
                    "type": cluster_type,
                    "keywords": top_cluster_keywords['keyword'].tolist(),
                    "avg_views": avg_view,
                    "avg_view_to_menu": avg_v2m,
                    "avg_menu_to_checkout": avg_m2c,
                    "avg_checkout_to_order": avg_c2o,
                    "count": len(cluster_df)
                })

        except Exception as e:
            # If clustering fails, just note the error but continue
            clusters = {"error": f"Could not perform clustering: {str(e)}"}

    # Opportunities and recommendations
    opportunities = []
    recommendations = []

    # Find keywords with high views but low conversion
    high_potential = relevant_df[(relevant_df['view'] > relevant_df['view'].median()) &
                                 (relevant_df['overall_conversion'] < relevant_df['overall_conversion'].median())]

    if not high_potential.empty:
        opportunities.append(f"Keywords with high search volume but low conversion: {', '.join(high_potential['keyword'].head(3))}")
        recommendations.append("Optimize menu items or descriptions to better match these popular search terms")

    # Find popular keywords not well-represented in the menu
    all_item_text = ' '.join(merchant_items['item_name']).lower()
    poorly_represented = []

    for _, row in top_searched.head(5).iterrows():
        keyword = str(row['keyword']).lower()
        if keyword not in all_item_text and row['view'] > 100:
            poorly_represented.append(keyword)

    if poorly_represented:
        opportunities.append(f"Popular search terms not prominently featured in your menu: {', '.join(poorly_represented)}")
        recommendations.append("Consider adding menu items or updating descriptions to feature these popular search terms")

    # Find high-converting but low-volume keywords
    hidden_gems = relevant_df[(relevant_df['overall_conversion'] > relevant_df['overall_conversion'].quantile(0.75)) &
                              (relevant_df['view'] < relevant_df['view'].median())]

    if not hidden_gems.empty:
        opportunities.append(f"Keywords with high conversion but low search volume: {', '.join(hidden_gems['keyword'].head(3))}")
        recommendations.append("Consider promoting these high-converting items more prominently")

    # Identify seasonal or trending keywords
    # In a real system, we'd have timestamp data to identify trends
    # Here we'll just use a proxy (high conversion + high views) to simulate "trending" items
    trending = relevant_df[(relevant_df['view'] > relevant_df['view'].quantile(0.75)) &
                           (relevant_df['overall_conversion'] > relevant_df['overall_conversion'].quantile(0.6))]

    trending_keywords = []
    if not trending.empty:
        trending_keywords = trending['keyword'].head(5).tolist()
        opportunities.append(f"Trending search terms with good conversion: {', '.join(trending_keywords)}")
        recommendations.append("Feature these trending items prominently in promotions and front page")

    return {
        "relevant_keywords_count": len(relevant_df),
        "top_searched_keywords": top_searched.to_dict(orient='records'),
        "best_converting_keywords": best_converting.to_dict(orient='records'),
        "high_abandonment_keywords": high_abandonment.to_dict(orient='records'),
        "keyword_clusters": clusters,
        "opportunities": opportunities,
        "recommendations": recommendations,
        "trending_keywords": trending_keywords
    }

def generate_bottleneck(merchant_id, transaction_df, inventory_insights, sales_insights, benchmark_insights):
    """Identify operational bottlenecks from wait time, inventory, and sales patterns"""
    merchant_txns = transaction_df[transaction_df['merchant_id'] == merchant_id]
    bottlenecks = []

    # --- Wait Time Analysis ---
    if not merchant_txns.empty and 'wait_time' in merchant_txns.columns:
        wait_time_stats = merchant_txns['wait_time'].describe().to_dict()
        avg_wait = wait_time_stats.get('mean', None)
        max_wait = wait_time_stats.get('max', None)

        if avg_wait and avg_wait > 25:
            bottlenecks.append(f"High average wait time ({avg_wait:.1f} min) — possible kitchen or delivery delays.")
        if max_wait and max_wait > 60:
            bottlenecks.append(f"Long peak wait times reaching {max_wait:.1f} min — check capacity during rush hours.")

        # Benchmark comparison
        if 'metrics_detail' in benchmark_insights and 'wait_time' in benchmark_insights['metrics_detail']:
            peer_diff = benchmark_insights['metrics_detail']['wait_time']['difference_pct']
            if peer_diff > 10:
                bottlenecks.append(f"Wait time is {peer_diff:.1f}% longer than peers — operational speed may be below standard.")
    else:
        wait_time_stats = {"note": "Wait time data not available"}

    # --- Slow Moving Items ---
    if 'slow_movers' in inventory_insights and not inventory_insights['slow_movers'].empty:
        slow_items = inventory_insights['slow_movers'].head(3)
        for _, item in slow_items.iterrows():
            bottlenecks.append(f"Slow-moving item: {item['item_name']} with only {item['order_count']} orders.")

    # --- Low-performing Hours ---
    if 'hourly_trends' in sales_insights and not sales_insights['hourly_trends'].empty:
        low_hours = sales_insights['hourly_trends'].nsmallest(3, 'order_count')
        for _, hour in low_hours.iterrows():
            bottlenecks.append(f"Low order volume at {int(hour['hour_of_day'])}:00 — consider promotions or review staffing.")

    # --- Low-performing Days ---
    if 'daily_trends' in sales_insights and not sales_insights['daily_trends'].empty:
        low_days = sales_insights['daily_trends'].nsmallest(2, 'total_sales')
        for _, day in low_days.iterrows():
            bottlenecks.append(f"{day['day_of_week']} has low sales (RM{day['total_sales']:.2f}) — explore discounts or campaigns.")

    return {
        "wait_time_stats": wait_time_stats,
        "bottlenecks": bottlenecks if bottlenecks else ["No major bottlenecks detected from current insights."]
    }


from together import Together

class LLMResponder:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        self.model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"

    def get_response(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant who explains business insights to merchants in simple terms. Use friendly and actionable language."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Sorry, I couldn't generate a response due to an error: {e}"

class SmartMerchantAssistant:
    def __init__(self, merchant_id, merchant_df, items_df, transaction_df, transaction_item_df, keyword_df=None):
        self.merchant_id = merchant_id
        self.merchant_df = merchant_df
        self.items_df = items_df
        self.transaction_df = transaction_df
        self.transaction_item_df = transaction_item_df
        self.keyword_df = keyword_df

        import os
        api_key = os.environ.get("TOGETHER_API_KEY", "e9d4a2f1ab1492bab4ab7525746160deb428cbf743c7528ec6b6392fcdc2b593")
        self.llm = LLMResponder(api_key)

        # Load all insights
        self.sales_insights = generate_sales_insights(merchant_id, transaction_df)
        self.inventory_insights = generate_inventory_insights(merchant_id, transaction_item_df, items_df)
        self.customer_insights = generate_customer_insights(merchant_id, transaction_df)
        self.benchmark_insights = generate_benchmark_insights(merchant_id, merchant_df, transaction_df, items_df)
        self.location_insights = generate_location_insights(merchant_id, merchant_df, transaction_df, items_df, transaction_item_df)
        self.keyword_insights = None
        if keyword_df is not None:
            self.keyword_insights = generate_keyword_insights(merchant_id, transaction_item_df, items_df, keyword_df)
        self.bottleneck_insights = generate_bottleneck(merchant_id,transaction_df,self.inventory_insights,self.sales_insights,self.benchmark_insights)

    def get_context_summary(self):
        """Summarize key business data to include in prompt"""
        try:
            context = []

            # 🧾 Sales
            context.append(f"Sales in last 30 days: RM{self.sales_insights['recent_performance']:.2f}.")
            best_day = self.sales_insights['best_days'].iloc[0]
            context.append(f"Best performing day: {best_day['day_of_week']} (RM{best_day['total_sales']:.2f}).")

            # Peak hour
            context.append(f"Peak Hours: {self.sales_insights['peak_hours']}")

            context.append(f"Daily trends: {self.sales_insights['daily_trends']}")
            context.append(f"Hourly trends: {self.sales_insights['hourly_trends']}")
            context.append(f"Best-performing days: {self.sales_insights['best_days']}")
            context.append(f"Monthly sales: {self.sales_insights['monthly_sales']}")
            context.append(f"Wait time stats: {self.sales_insights['wait_time_stats']}")

            # Add sales forecast information
            context.append("Sales forecast for next 7 days (in RM):")
            for i, amount in enumerate(self.sales_insights['sales_forecast']):
                context.append(f"Day {i+1}: RM{amount:.2f}")

            context.append(f"Sales trend: {self.sales_insights['sales_trend']}.")
            if self.sales_insights['sales_growth_rate'] is not None:
                context.append(f"Growth rate: {self.sales_insights['sales_growth_rate']:.1f}%.")

            # Include comparison data
            context.append(f"Last 7 days sales: RM{self.sales_insights['last_7_days_sales']:.2f} ({self.sales_insights['last_7_days_orders']} orders)")
            context.append(f"Last 30 days sales: RM{self.sales_insights['last_30_days_sales']:.2f} ({self.sales_insights['last_30_days_orders']} orders)")
            context.append(f"Previous 30 days sales: RM{self.sales_insights['prev_30_days_sales']:.2f}")

            # 📦 Inventory
            if not self.inventory_insights['top_sellers'].empty:
                top_item = self.inventory_insights['top_sellers'].iloc[0]
                context.append(f"Top selling item: {top_item['item_name']} ({top_item['order_count']} orders).")
                slow_item = self.inventory_insights['slow_movers'].iloc[0]
                context.append(f"Slow moving item: {slow_item['item_name']} ({slow_item['order_count']} orders).")
                profitable_item = self.inventory_insights['profitable_items'].iloc[0]
                context.append(f"Most profitable item: {profitable_item['item_name']} (RM{profitable_item['revenue']:.2f}).")
                item_performance = self.inventory_insights['item_performance']
                context.append(f"Item performance: {item_performance}")
                context.append(f"High margin items: {self.inventory_insights['high_margin_items']}")
                common_pairs = self.inventory_insights['common_pairs']
                context.append(f"Common item pairs: {common_pairs}")
                price_distribution = self.inventory_insights['price_distribution']
                context.append(f"Price distribution: {price_distribution}")
                context.append(f"Total items: {self.inventory_insights['total_items']}.")
                context.append(f"Active items: {self.inventory_insights['active_items']}.")


            # 🧑‍🤝‍🧑 Customers
            if 'error' in self.customer_insights:
                context.append(f"Customer Stats Error: {self.customer_insights['error']}")
            else:
                context.append(f"Total customers: {self.customer_insights['total_customers']}.")
                context.append(f"Repeat customers: {self.customer_insights['repeat_customers']} ({self.customer_insights['repeat_customer_percentage']:.1f}%).")

                if 'high_value_customers' in self.customer_insights and not self.customer_insights['high_value_customers'].empty:
                    top_customer = self.customer_insights['high_value_customers'].iloc[0]
                    context.append(f"Top customer spent: RM{top_customer['total_spent']:.2f}.")
                    context.append(f"Top customer average order: RM{top_customer['avg_order_value']:.2f}.")

                if 'segment_distribution' in self.customer_insights:
                    context.append(f"Customer segments: {self.customer_insights['segment_distribution']}")

                if 'overall_retention' in self.customer_insights:
                    context.append(f"Overall retention rate: {self.customer_insights['overall_retention']:.1%}")

                if 'new_customers_by_month' in self.customer_insights and not self.customer_insights['new_customers_by_month'].empty:
                    last_month = self.customer_insights['new_customers_by_month'].iloc[-1]
                    context.append(f"New customers in last month: {last_month['new_customers']}")

                if 'aov_by_month' in self.customer_insights and not self.customer_insights['aov_by_month'].empty:
                    last_month_aov = self.customer_insights['aov_by_month'].iloc[-1]
                    context.append(f"Last month average order value: RM{last_month_aov['avg_order_value']:.2f}")

                if 'cohort_retention' in self.customer_insights and not self.customer_insights['cohort_retention'].empty:
                    # Get the most recent cohort's 1-month retention
                    recent_cohorts = self.customer_insights['cohort_retention']
                    one_month_retention = recent_cohorts[recent_cohorts['months_since_first_order'] == 1]
                    if not one_month_retention.empty:
                        latest_retention = one_month_retention.iloc[-1]
                        context.append(f"First month retention rate: {latest_retention['retention_rate']:.1%}")

                if 'delivery_time_by_customer' in self.customer_insights:
                    avg_delivery_time = self.customer_insights['delivery_time_by_customer']['avg_wait_time'].mean()
                    context.append(f"Average delivery time: {avg_delivery_time:.1f} minutes")

                # benchmark
                context.append(f"Benchmarking: {self.benchmark_insights}")

            # 📍 Location insights
            if 'error' in self.location_insights:
                context.append(f"Location Insights Error: {self.location_insights['error']}")
            else:
                context.append(f"City ID: {self.location_insights['merchant_city_id']}")
                context.append(f"Total merchants in city: {self.location_insights['city_merchant_count']}")
                context.append(f"Your sales rank in city: {self.location_insights['merchant_sales_rank']} out of {self.location_insights['merchants_in_city']}")

                if 'category_performance' in self.location_insights and self.location_insights['category_performance'] is not None and not self.location_insights['category_performance'].empty:
                    best_categories = self.location_insights['category_performance'].iloc[0:3]
                    worst_categories = self.location_insights['category_performance'].iloc[-3:]
                    context.append(f"Best performing categories in city: {list(best_categories[best_categories.columns[0]])}")
                    context.append(f"Worst performing categories in city: {list(worst_categories[worst_categories.columns[0]])}")

                if 'best_city_items' in self.location_insights and not self.location_insights['best_city_items'].empty:
                    best_items = self.location_insights['best_city_items'].iloc[0:3]
                    context.append(f"Best selling items in city: {list(best_items['item_name'])}")

                if 'worst_city_items' in self.location_insights and not self.location_insights['worst_city_items'].empty:
                    worst_items = self.location_insights['worst_city_items'].iloc[0:3]
                    context.append(f"Worst selling items in city: {list(worst_items['item_name'])}")

                if 'relative_sales' in self.location_insights:
                    rel_sales = self.location_insights['relative_sales']
                    context.append(f"Your sales: RM{rel_sales['merchant_sales']:.2f}")
                    context.append(f"City average sales: RM{rel_sales['city_average']:.2f}")
                    context.append(f"City top performer sales: RM{rel_sales['city_top']:.2f}")

                if 'opportunities' in self.location_insights and self.location_insights['opportunities']:
                    context.append(f"Location-based opportunities: {self.location_insights['opportunities']}")

                if 'strengths' in self.location_insights and self.location_insights['strengths']:
                    context.append(f"Location-based strengths: {self.location_insights['strengths']}")

                # 🔍 Keyword Insights
                if self.keyword_insights:
                    if 'error' in self.keyword_insights:
                        context.append(f"Keyword Insights Error: {self.keyword_insights['error']}")
                    else:
                        context.append(f"Number of relevant keywords: {self.keyword_insights['relevant_keywords_count']}")

                        if 'top_searched_keywords' in self.keyword_insights and self.keyword_insights['top_searched_keywords']:
                            top_keywords = [k['keyword'] for k in self.keyword_insights['top_searched_keywords'][:3]]
                            context.append(f"Most searched keywords: {', '.join(top_keywords)}")

                        if 'best_converting_keywords' in self.keyword_insights and self.keyword_insights['best_converting_keywords']:
                            best_keywords = [k['keyword'] for k in self.keyword_insights['best_converting_keywords'][:3]]
                            context.append(f"Best converting keywords: {', '.join(best_keywords)}")

                        if 'high_abandonment_keywords' in self.keyword_insights and self.keyword_insights['high_abandonment_keywords']:
                            abandoned_keywords = [k['keyword'] for k in self.keyword_insights['high_abandonment_keywords'][:3]]
                            context.append(f"Keywords with high abandonment: {', '.join(abandoned_keywords)}")

                        if 'keyword_clusters' in self.keyword_insights and self.keyword_insights['keyword_clusters']:
                            clusters = self.keyword_insights['keyword_clusters']
                            if isinstance(clusters, list):
                                for cluster in clusters[:2]:  # Just include first 2 clusters
                                    context.append(f"Keyword group - {cluster['type']}: {', '.join(cluster['keywords'][:3])}")

                        if 'trending_keywords' in self.keyword_insights and self.keyword_insights['trending_keywords']:
                            context.append(f"Trending keywords: {', '.join(self.keyword_insights['trending_keywords'][:5])}")

                        if 'opportunities' in self.keyword_insights and self.keyword_insights['opportunities']:
                            context.append(f"Keyword opportunities: {self.keyword_insights['opportunities']}")

                        if 'recommendations' in self.keyword_insights and self.keyword_insights['recommendations']:
                            context.append(f"Keyword recommendations: {self.keyword_insights['recommendations']}")

                    # ⚠️ Bottlenecks
                    context.append("\n🔍 Operational Bottlenecks:")
                    if 'bottlenecks' in self.bottleneck_insights:
                        for issue in self.bottleneck_insights['bottlenecks']:
                            context.append(f"- {issue}")

            return "\n".join(context)
        except Exception as e:
            return "No context summary available due to error."

    def handle_query(self, user_query):
        """Combine query + insights into a prompt and send to LLM"""
        context = self.get_context_summary()
        full_prompt = f"""
        Merchant Question: {user_query}

        Business Overview:
        {context}

        Please answer the merchant's question using the above information. Make it easy to understand and provide actionable advice.
        """
        return self.llm.get_response(full_prompt)