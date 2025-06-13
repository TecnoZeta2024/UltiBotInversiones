-- Migration: Create AI Prompts Management System
-- Version: 003
-- Description: Tabla para gestión dinámica de prompts con versionado completo
-- Author: Cline - AI Orchestrator System
-- Date: 2025-06-11

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ai_prompts table with versioning support
CREATE TABLE IF NOT EXISTS ai_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    template TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system',
    tags TEXT[] DEFAULT '{}',
    
    -- Ensure unique name-version combination
    UNIQUE(name, version)
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_ai_prompts_name ON ai_prompts(name);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_active ON ai_prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_category ON ai_prompts(category);
CREATE INDEX IF NOT EXISTS idx_ai_prompts_created_at ON ai_prompts(created_at);

-- Create function to get latest version of a prompt
CREATE OR REPLACE FUNCTION get_latest_prompt_version(prompt_name VARCHAR)
RETURNS ai_prompts AS $$
DECLARE
    result ai_prompts;
BEGIN
    SELECT * INTO result
    FROM ai_prompts
    WHERE name = prompt_name 
      AND is_active = true
    ORDER BY version DESC
    LIMIT 1;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to create new prompt version
CREATE OR REPLACE FUNCTION create_prompt_version(
    prompt_name VARCHAR,
    new_template TEXT,
    new_variables JSONB DEFAULT '{}',
    new_description TEXT DEFAULT NULL,
    new_category VARCHAR DEFAULT 'general',
    creator VARCHAR DEFAULT 'system'
)
RETURNS ai_prompts AS $$
DECLARE
    next_version INTEGER;
    result ai_prompts;
BEGIN
    -- Get next version number
    SELECT COALESCE(MAX(version), 0) + 1 INTO next_version
    FROM ai_prompts
    WHERE name = prompt_name;
    
    -- Deactivate current active version
    UPDATE ai_prompts 
    SET is_active = false, updated_at = NOW()
    WHERE name = prompt_name AND is_active = true;
    
    -- Create new version
    INSERT INTO ai_prompts (
        name, version, template, variables, description, 
        category, is_active, created_by
    ) VALUES (
        prompt_name, next_version, new_template, new_variables, 
        new_description, new_category, true, creator
    ) RETURNING * INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Insert default prompts for the system
INSERT INTO ai_prompts (name, version, template, variables, description, category, tags) VALUES

-- 1. Opportunity Planning Prompt
('opportunity_planning', 1, 
'# TRADING OPPORTUNITY ANALYSIS PLANNING

## CONTEXT
You are an expert trading AI analyzing a potential opportunity. Your task is to create a comprehensive analysis plan.

## OPPORTUNITY DATA
Symbol: {{ symbol }}
Current Price: {{ current_price }}
24h Change: {{ price_change_24h }}%
Volume: {{ volume_24h }}
Market Cap: {{ market_cap }}

## AVAILABLE TOOLS
{{ available_tools }}

## ANALYSIS PLANNING TASK
Create a detailed plan to analyze this opportunity. Consider:

1. **Technical Analysis**: What indicators and timeframes to examine
2. **Fundamental Analysis**: Key metrics and news to research  
3. **Sentiment Analysis**: Social and market sentiment sources
4. **Risk Assessment**: Potential risks and mitigation strategies
5. **Tool Selection**: Which tools to use and in what order

## OUTPUT FORMAT
Provide a structured analysis plan with:
- Tool execution sequence
- Expected insights from each tool
- Decision criteria for trade recommendation
- Risk management parameters

Plan thoughtfully and comprehensively.',
'{"symbol": "string", "current_price": "number", "price_change_24h": "number", "volume_24h": "number", "market_cap": "number", "available_tools": "array"}',
'Prompt para planificar análisis completo de oportunidades de trading',
'trading',
ARRAY['planning', 'analysis', 'trading']),

-- 2. Opportunity Synthesis Prompt
('opportunity_synthesis', 1,
'# TRADING OPPORTUNITY SYNTHESIS

## CONTEXT
Based on comprehensive analysis using multiple tools, synthesize findings into actionable trading recommendation.

## ORIGINAL OPPORTUNITY
Symbol: {{ symbol }}
Entry Context: {{ entry_context }}

## ANALYSIS RESULTS
{{ tool_results }}

## SYNTHESIS TASK
Combine all analysis results into a final recommendation considering:

1. **Technical Confluence**: How multiple indicators align
2. **Fundamental Strength**: Overall asset health and prospects
3. **Market Sentiment**: Crowd psychology and positioning
4. **Risk/Reward Ratio**: Potential gains vs. potential losses
5. **Timing Assessment**: Optimal entry/exit points

## OUTPUT FORMAT
Provide structured recommendation:

```json
{
    "recommendation": "BUY|SELL|HOLD|AVOID",
    "confidence": 0.85,
    "entry_price": 45.50,
    "target_price": 52.00,
    "stop_loss": 42.00,
    "position_size": 0.02,
    "time_horizon": "3-7 days",
    "key_reasons": ["reason1", "reason2", "reason3"],
    "risk_factors": ["risk1", "risk2"],
    "exit_conditions": ["condition1", "condition2"]
}
```

Be precise, objective, and actionable.',
'{"symbol": "string", "entry_context": "string", "tool_results": "object"}',
'Prompt para sintetizar análisis múltiple en recomendación de trading',
'trading',
ARRAY['synthesis', 'recommendation', 'trading']),

-- 3. Strategy Analysis Prompt
('strategy_analysis', 1,
'# TRADING STRATEGY PERFORMANCE ANALYSIS

## CONTEXT
Analyze the performance and effectiveness of a trading strategy based on historical data and current market conditions.

## STRATEGY DATA
Strategy Name: {{ strategy_name }}
Parameters: {{ strategy_parameters }}
Historical Performance: {{ historical_performance }}
Current Market Conditions: {{ market_conditions }}

## ANALYSIS FOCUS
Evaluate the strategy across multiple dimensions:

1. **Performance Metrics**
   - Win rate and average win/loss ratio
   - Maximum drawdown and recovery time
   - Sharpe ratio and risk-adjusted returns
   - Consistency across different market regimes

2. **Market Regime Analysis**
   - Performance in trending vs. ranging markets
   - Volatility sensitivity
   - Correlation with market indices
   - Sector/asset class effectiveness

3. **Parameter Sensitivity**
   - Robustness to parameter changes
   - Optimal parameter ranges
   - Overfitting risk assessment

4. **Current Suitability**
   - Alignment with current market conditions
   - Recent performance trends
   - Recommended adjustments

## OUTPUT FORMAT
Provide comprehensive strategy assessment:

```json
{
    "overall_rating": "A+|A|B+|B|C+|C|D",
    "key_strengths": ["strength1", "strength2"],
    "key_weaknesses": ["weakness1", "weakness2"],
    "market_suitability": "HIGH|MEDIUM|LOW",
    "recommended_allocation": 0.15,
    "parameter_adjustments": {"param1": "new_value"},
    "monitoring_points": ["point1", "point2"],
    "exit_criteria": ["criteria1", "criteria2"]
}
```',
'{"strategy_name": "string", "strategy_parameters": "object", "historical_performance": "object", "market_conditions": "object"}',
'Prompt para análisis profundo de performance de estrategias de trading',
'strategy',
ARRAY['strategy', 'performance', 'analysis']),

-- 4. Risk Assessment Prompt  
('risk_assessment', 1,
'# COMPREHENSIVE RISK ASSESSMENT

## CONTEXT
Conduct thorough risk analysis for a trading opportunity or portfolio position.

## POSITION DATA
Asset: {{ asset }}
Position Size: {{ position_size }}
Entry Price: {{ entry_price }}
Current Price: {{ current_price }}
Portfolio Context: {{ portfolio_context }}

## RISK ANALYSIS FRAMEWORK

### 1. MARKET RISK
- Price volatility and historical ranges
- Correlation with major indices
- Sector-specific risks
- Liquidity considerations

### 2. FUNDAMENTAL RISK  
- Company/protocol specific risks
- Regulatory environment
- Competitive landscape
- Economic sensitivity

### 3. TECHNICAL RISK
- Support/resistance levels
- Trend strength and sustainability
- Volume profile analysis
- Chart pattern completion risk

### 4. PORTFOLIO RISK
- Concentration risk
- Correlation with existing positions
- Overall portfolio volatility
- Diversification impact

### 5. OPERATIONAL RISK
- Execution risk and slippage
- Exchange/platform risk
- Custody considerations
- Technology dependencies

## OUTPUT FORMAT
Provide structured risk assessment:

```json
{
    "overall_risk_score": 6.5,
    "risk_category": "MODERATE",
    "key_risks": [
        {"type": "market", "severity": "HIGH", "description": "High correlation with BTC"},
        {"type": "liquidity", "severity": "MEDIUM", "description": "Lower volume in Asian hours"}
    ],
    "risk_mitigation": [
        "Reduce position size by 25%",
        "Set tighter stop loss at $42.50"
    ],
    "monitoring_alerts": [
        "BTC correlation above 0.8",
        "Volume drops below 50% of 30-day average"
    ],
    "maximum_loss_scenario": "$2,450",
    "probability_of_loss": 0.35
}
```

Be thorough, quantitative where possible, and actionable.',
'{"asset": "string", "position_size": "number", "entry_price": "number", "current_price": "number", "portfolio_context": "object"}',
'Prompt para evaluación comprehensiva de riesgos en trading',
'risk',
ARRAY['risk', 'assessment', 'portfolio']),

-- 5. Market Sentiment Prompt
('market_sentiment', 1,
'# MARKET SENTIMENT ANALYSIS

## CONTEXT
Analyze current market sentiment across multiple dimensions to inform trading decisions.

## MARKET DATA
Asset: {{ asset }}
Timeframe: {{ timeframe }}
Sentiment Sources: {{ sentiment_sources }}

## SENTIMENT ANALYSIS DIMENSIONS

### 1. SOCIAL SENTIMENT
- Twitter/X mentions and sentiment
- Reddit discussion volume and tone
- Discord/Telegram community activity
- Influencer opinions and positions

### 2. ON-CHAIN SENTIMENT (for crypto)
- Whale movements and accumulation
- Exchange inflows/outflows
- Long-term holder behavior
- Network activity metrics

### 3. TECHNICAL SENTIMENT
- Fear & Greed Index
- Put/Call ratios
- VIX and volatility measures
- Market breadth indicators

### 4. INSTITUTIONAL SENTIMENT
- Fund flows and positioning
- Analyst upgrades/downgrades
- Insider trading activity
- Corporate actions and announcements

### 5. NEWS SENTIMENT
- News article sentiment analysis
- Press release impact
- Regulatory developments
- Macroeconomic factors

## ANALYSIS TASK
Synthesize sentiment data to provide actionable insights:

1. **Current Sentiment State**: Bullish/Bearish/Neutral with confidence
2. **Sentiment Momentum**: Direction and speed of change
3. **Contrarian Signals**: Extreme sentiment levels for contrarian plays
4. **Catalyst Identification**: Events likely to shift sentiment
5. **Timeline Assessment**: How long current sentiment may persist

## OUTPUT FORMAT
```json
{
    "overall_sentiment": "BULLISH",
    "sentiment_score": 7.2,
    "confidence": 0.78,
    "momentum": "STRENGTHENING",
    "key_drivers": [
        "Positive whale accumulation",
        "Strong social media buzz",
        "Upcoming protocol upgrade"
    ],
    "contrarian_signals": [
        "Retail FOMO reaching extreme levels"
    ],
    "sentiment_targets": {
        "bullish_continuation": 8.5,
        "sentiment_exhaustion": 9.2,
        "bearish_reversal": 3.0
    },
    "recommended_action": "CAUTIOUS_BULLISH",
    "monitoring_points": [
        "Social mentions volume",
        "Whale wallet activity",
        "Options skew changes"
    ]
}
```

Focus on actionable insights and quantifiable metrics.',
'{"asset": "string", "timeframe": "string", "sentiment_sources": "array"}',
'Prompt para análisis completo de sentimiento de mercado multi-dimensional',
'sentiment',
ARRAY['sentiment', 'market', 'social', 'analysis']);

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER update_ai_prompts_updated_at
    BEFORE UPDATE ON ai_prompts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for active prompts
CREATE OR REPLACE VIEW active_prompts AS
SELECT 
    id,
    name,
    version,
    template,
    variables,
    description,
    category,
    created_at,
    updated_at,
    created_by,
    tags
FROM ai_prompts
WHERE is_active = true
ORDER BY name, version DESC;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON ai_prompts TO ultibot_user;
-- GRANT USAGE ON SEQUENCE ai_prompts_id_seq TO ultibot_user;
-- GRANT SELECT ON active_prompts TO ultibot_user;

COMMIT;
