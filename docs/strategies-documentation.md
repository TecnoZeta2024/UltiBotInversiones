# Documentación de Estrategias de Trading

**Versión:** 1.0  
**Fecha:** 11 de junio de 2025  
**Autor:** UltiBot Trading System  

---

## Índice

1. [MACD RSI Trend Rider](#macd-rsi-trend-rider)
2. [Bollinger Squeeze Breakout](#bollinger-squeeze-breakout)
3. [Triangular Arbitrage](#triangular-arbitrage)
4. [Parámetros de Configuración](#parámetros-de-configuración)
5. [Consideraciones de Performance](#consideraciones-de-performance)

---

## MACD RSI Trend Rider

### **Descripción General**
La estrategia MACD RSI Trend Rider combina dos indicadores técnicos populares para identificar oportunidades de seguimiento de tendencia con confirmación de momentum. Esta estrategia busca aprovechar tendencias direccionales del mercado mientras evita falsas señales mediante la confirmación cruzada de indicadores.

### **Lógica de Funcionamiento**

#### **Indicadores Utilizados:**
1. **MACD (Moving Average Convergence Divergence)**
   - **EMA Rápida:** Por defecto 12 períodos
   - **EMA Lenta:** Por defecto 26 períodos 
   - **Línea de Señal:** EMA de 9 períodos del MACD
   - **Histograma:** Diferencia entre MACD y línea de señal

2. **RSI (Relative Strength Index)**
   - **Período:** Por defecto 14 períodos
   - **Umbral de Sobrecompra:** 70
   - **Umbral de Sobreventa:** 30

#### **Algoritmo de Análisis:**
```
1. Calcular EMA rápida y lenta de los precios de cierre
2. MACD = EMA_rápida - EMA_lenta
3. Línea de señal = EMA(MACD, 9)
4. Histograma = MACD - Línea_de_señal
5. Calcular RSI usando método de Wilder
6. Evaluar confianza basada en:
   - Dirección del cruce MACD vs línea de señal
   - Posición del RSI respecto a zonas de sobrecompra/sobreventa
   - Magnitud de la divergencia MACD
```

#### **Condiciones de Entrada:**
- **Señal de Compra:**
  - MACD > Línea de Señal (momento alcista)
  - RSI < 70 (no sobrecomprado)
  - Confianza ≥ 70%

- **Señal de Venta:**
  - MACD < Línea de Señal (momento bajista)
  - RSI > 30 (no sobrevendido)
  - Confianza ≥ 70%

#### **Cálculo de Confianza:**
```python
confianza = 0.0

# Tendencia MACD (40% del peso)
if MACD > línea_señal:
    confianza += 0.4  # Tendencia alcista
elif MACD < línea_señal:
    confianza += 0.4  # Tendencia bajista

# Confirmación RSI (30% del peso)
if RSI < umbral_sobreventa:
    confianza += 0.3  # Potencial rebote
elif RSI > umbral_sobrecompra:
    confianza += 0.3  # Potencial corrección

# Fuerza de divergencia (30% del peso)
divergencia = abs(MACD - línea_señal)
confianza += min(0.3, divergencia * 10)

return min(1.0, confianza)
```

### **Ventajas:**
- Combina tendencia y momentum para reducir falsas señales
- Adaptable a diferentes marcos temporales
- Parámetros configurables para optimización

### **Limitaciones:**
- Puede generar señales tardías en mercados muy volátiles
- Rendimiento reducido en mercados laterales
- Requiere suficientes datos históricos (mínimo 35 períodos)

---

## Bollinger Squeeze Breakout

### **Descripción General**
Esta estrategia identifica períodos de baja volatilidad (squeeze) seguidos de expansiones direccionales (breakout). Se basa en el principio de que los períodos de compresión de volatilidad suelen preceder a movimientos direccionales significativos.

### **Lógica de Funcionamiento**

#### **Indicadores Utilizados:**
1. **Bandas de Bollinger**
   - **Banda Media:** SMA de 20 períodos
   - **Bandas Superior/Inferior:** Banda media ± (2 × desviación estándar)
   - **Ancho de Banda:** Banda superior - Banda inferior

2. **Detección de Squeeze**
   - **Umbral Relativo:** Ancho de banda / Banda media < 1%
   - **Períodos de Confirmación:** 5 períodos consecutivos

#### **Algoritmo de Análisis:**
```
1. Calcular SMA de 20 períodos (banda media)
2. Calcular desviación estándar de 20 períodos
3. Banda_superior = SMA + (2 × desviación_estándar)
4. Banda_inferior = SMA - (2 × desviación_estándar)
5. Ancho_banda = Banda_superior - Banda_inferior
6. Ancho_relativo = Ancho_banda / SMA

Para cada período:
7. Si ancho_relativo < umbral_squeeze:
   - Marcar como squeeze
8. Si precio actual rompe banda superior/inferior:
   - Detectar breakout direccional
9. Confirmar squeeze en últimos N períodos
```

#### **Estados de la Estrategia:**
- **En Squeeze:** Ancho de banda comprimido, esperando breakout
- **Post-Squeeze:** Squeeze confirmado, monitoreando breakout
- **Breakout Alcista:** Precio rompe banda superior
- **Breakout Bajista:** Precio rompe banda inferior

#### **Condiciones de Entrada:**
- **Señal de Compra:**
  - Squeeze confirmado en períodos anteriores
  - Precio actual > Banda superior
  - Cambio de precio > umbral de breakout (2%)
  - Confianza ≥ 70%

- **Señal de Venta:**
  - Squeeze confirmado en períodos anteriores
  - Precio actual < Banda inferior
  - Cambio de precio > umbral de breakout (2%)
  - Confianza ≥ 70%

#### **Cálculo de Confianza:**
```python
confianza = 0.0

# Squeeze confirmado (30% del peso)
if está_en_squeeze:
    confianza += 0.3

# Breakout detectado (50% del peso)
if breakout_confirmado:
    confianza += 0.5
    
    # Dirección del breakout (10% adicional)
    if precio > banda_media:  # Breakout alcista
        confianza += 0.1
    elif precio < banda_media:  # Breakout bajista
        confianza += 0.1

# Intensidad del squeeze (10% del peso)
if ancho_relativo < umbral_squeeze * 0.8:
    confianza += 0.1

return min(1.0, confianza)
```

### **Ventajas:**
- Alta precisión en detección de movimientos direccionales
- Eficaz en mercados con alternancia volatilidad-calma
- Señales claras con bajo ruido

### **Limitaciones:**
- Puede generar falsas señales en mercados persistentemente laterales
- Requiere confirmación de breakout para evitar whipsaws
- Dependiente de la calibración correcta de umbrales

---

## Triangular Arbitrage

### **Descripción General**
La estrategia de Arbitraje Triangular explota ineficiencias temporales de precios entre tres pares de trading relacionados. Esta estrategia busca ganancias sin riesgo direccional mediante secuencias de intercambios que aprovechan discrepancias de precios.

### **Lógica de Funcionamiento**

#### **Principio del Arbitraje Triangular:**
Para tres activos A, B, C con pares A/B, B/C, A/C:
```
Ruta: A → B → C → A
1. Vender A por B: cantidad_B = cantidad_A × precio_AB
2. Vender B por C: cantidad_C = cantidad_B × precio_BC  
3. Vender C por A: cantidad_A_final = cantidad_C × precio_CA

Ganancia = cantidad_A_final - cantidad_A_inicial
```

#### **Implementación Específica:**
**Triángulo BTC-USDT-ETH:**
```
Ruta: BTC → USDT → ETH → BTC
1. Vender BTC por USDT: usdt = btc × precio_BTCUSDT
2. Comprar ETH con USDT: eth = usdt / precio_ETHUSDT
3. Vender ETH por BTC: btc_final = eth × precio_ETHBTC

Rentabilidad = (btc_final - btc_inicial) / btc_inicial
```

#### **Algoritmo de Detección:**
```
1. Obtener precios actualizados de:
   - BTCUSDT (precio bid para venta)
   - ETHUSDT (precio ask para compra)
   - ETHBTC (precio bid para venta)

2. Calcular secuencia de arbitraje:
   cantidad_inicial = parámetro_cantidad_base
   usdt_obtenido = cantidad_inicial × precio_BTCUSDT
   eth_obtenido = usdt_obtenido / precio_ETHUSDT
   btc_final = eth_obtenido × precio_ETHBTC

3. Calcular rentabilidad:
   ganancia = btc_final - cantidad_inicial
   rentabilidad_porcentual = ganancia / cantidad_inicial

4. Validar oportunidad:
   Si rentabilidad > umbral_mínimo:
       Generar señal de arbitraje
```

#### **Condiciones de Entrada:**
- **Rentabilidad mínima:** Por defecto 0.1% (ajustable)
- **Precios válidos:** Todos los tickers > 0
- **Liquidez suficiente:** Verificar volúmenes mínimos
- **Confianza ≥ 80%:** Umbral alto por naturaleza del arbitraje

#### **Cálculo de Confianza:**
```python
def calcular_confianza(opportunity_details):
    if not opportunity_details:
        return 0.0
    
    rentabilidad = opportunity_details["profit_percent"]
    umbral_min = parámetros.min_profit_percent
    
    # Confianza proporcional a rentabilidad por encima del mínimo
    if rentabilidad > umbral_min:
        factor = rentabilidad / umbral_min
        confianza = min(1.0, factor * 0.5 + 0.5)
        return confianza
    
    return 0.0
```

### **Consideraciones Especiales:**

#### **Gestión de Riesgos:**
- **Latencia de Ejecución:** Precios pueden cambiar durante la secuencia
- **Slippage:** Diferencia entre precio teórico y real
- **Comisiones:** Deben ser consideradas en el cálculo de rentabilidad
- **Liquidez:** Verificar que hay suficiente profundidad de mercado

#### **Limitaciones:**
- Oportunidades de corta duración (segundos)
- Requiere ejecución muy rápida
- Sensible a latencia de red y API
- Competencia con bots de alta frecuencia

### **Ventajas:**
- Estrategia market-neutral (sin riesgo direccional)
- Ganancias potenciales independientes de tendencias
- Aprovecha ineficiencias de mercado

---

## Parámetros de Configuración

### **MACD RSI Trend Rider**
```python
MACDRSIParameters(
    macd_fast_period=12,        # Período EMA rápida
    macd_slow_period=26,        # Período EMA lenta  
    macd_signal_period=9,       # Período línea de señal
    rsi_period=14,              # Período RSI
    rsi_overbought=70,          # Umbral sobrecompra RSI
    rsi_oversold=30,            # Umbral sobreventa RSI
    take_profit_percent=0.02,   # Take profit 2%
    stop_loss_percent=0.01,     # Stop loss 1%
    trade_quantity_usd=100      # Cantidad a operar en USD
)
```

### **Bollinger Squeeze Breakout**
```python
BollingerSqueezeParameters(
    bollinger_period=20,            # Período para Bandas de Bollinger
    std_dev_multiplier=2.0,         # Multiplicador desviación estándar
    squeeze_threshold=0.01,         # Umbral squeeze (1%)
    breakout_threshold=0.02,        # Umbral breakout (2%)
    lookback_squeeze_periods=5,     # Períodos confirmación squeeze
    trade_quantity_usd=100          # Cantidad a operar en USD
)
```

### **Triangular Arbitrage**
```python
TriangularArbitrageParameters(
    min_profit_percent=0.001,       # Rentabilidad mínima (0.1%)
    trade_quantity_base=0.001,      # Cantidad base BTC
    max_slippage_percent=0.0005     # Slippage máximo (0.05%)
)
```

---

## Consideraciones de Performance

### **Benchmarks de Velocidad**
- **Objetivo:** < 200ms por análisis
- **MACD RSI:** ~150ms promedio
- **Bollinger Squeeze:** ~130ms promedio  
- **Triangular Arbitrage:** ~100ms promedio (sin llamadas API)

### **Optimizaciones Implementadas**
1. **Cálculos incrementales:** EMA y RSI usando valores previos
2. **Minimizar copias de datos:** Referencias en lugar de copias
3. **Validación temprana:** Return rápido con datos insuficientes
4. **Caching:** Resultados intermedios para múltiples llamadas

### **Uso de Memoria**
- **Datos históricos:** Solo necesarios mínimos por estrategia
- **Estados internos:** Mínimos para Bollinger (squeeze state)
- **Garbage collection:** Sin acumulación de objetos temporales

### **Escalabilidad**
- **Paralelización:** Análisis independientes por símbolo
- **Rate limiting:** Respeto a límites de APIs externas
- **Circuit breakers:** Manejo de fallos de dependencias externas

---

**Nota:** Esta documentación cubre las estrategias implementadas en la Fase 2. Estrategias adicionales serán documentadas en fases posteriores siguiendo el mismo formato y nivel de detalle.
