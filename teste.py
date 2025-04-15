from operator import inv
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
#import numpy_financial as npf

# Definindo fluxos de caixa
investimento = np.array([-1900, -1950, -2000])
receita_liquidam1 = np.array([630, 720, 810])
receita_liquidam2 = np.array([720, 830, 900])
receita_liquidam3 = np.array([800, 920, 1000])

# definindo taxa minima de atratividade
tmr = 0.10

# definindo o tempo do projeto
tempo_projeto = 4

probabilidades_sucesso_investimento = np.array([0.1, 0.1, 0.8])
proailidades_sucesso_receitam1 = np.array([0.15, 0.25, 0.60])
proailidades_sucesso_receitam2 = np.array([0.15, 0.25, 0.60])
proailidades_sucesso_receitam3 = np.array([0.15, 0.25, 0.60])

# calculo do investimento esperado
investimento_esperado = np.sum(
    investimento * probabilidades_sucesso_investimento)

# imprime o investimento esperado
print("Investimento Esperado:", investimento_esperado)

# calculo da receita esperada
receita_esperada1 = np.sum(receita_liquidam1 * proailidades_sucesso_receitam1)
receita_esperada2 = np.sum(receita_liquidam2 * proailidades_sucesso_receitam2)
receita_esperada3 = np.sum(receita_liquidam3 * proailidades_sucesso_receitam3)

# imprime a receita esperada
print("Receita Esperada 1:", receita_esperada1)
print("Receita Esperada 2:", receita_esperada2)
print("Receita Esperada 3:", receita_esperada3)

# calculo do valor presente liquido
vp1 = receita_esperada1 / (1 + tmr) ** 1
vp2 = receita_esperada2 / (1 + tmr) ** 2
vp3 = receita_esperada3 / (1 + tmr) ** 3

# imprime o valor presente liquido
print("Valor Presente Liquido ano 1:", vp1)
print("Valor Presente Liquido ano 2:", vp2)
print("Valor Presente Liquido ano 3:", vp3)

# calculo do valor presente liquido esperado
vpl_esperado = vp1 + vp2 + vp3 + investimento_esperado

# imprime o valor presente liquido esperado
print("Valor Presente Liquido Esperado:", vpl_esperado)

# calculo da probabilidade de sucesso
probabilidade_sucesso = np.sum(probabilidades_sucesso_investimento * proailidades_sucesso_receitam1 *
                               proailidades_sucesso_receitam2 * proailidades_sucesso_receitam3)

# imprime a probabilidade de sucesso
print("Probabilidade de Sucesso:", probabilidade_sucesso)

# variância do vpl esperado de cada contribuição do fluxo de caixa, representa a incerteza associada ao grau de dispersão da distribuição das frequências de ocorrencias.
varianciavplm0 = probabilidades_sucesso_investimento * \
    (investimento-investimento_esperado)**2
# some os valores de varianciavpl

varianciam0 = np.sum(varianciavplm0)

print("Variância do mês 0:", varianciam0)


# variância do vpl esperado de cada contribuição do fluxo de caixa, representa a incerteza associada ao grau de dispersão da distribuição das frequências de ocorrencias.
varianciam1 = proailidades_sucesso_receitam1 * \
    (receita_liquidam1-receita_esperada1)**2
varianciam2 = proailidades_sucesso_receitam2 * \
    (receita_liquidam2-receita_esperada2)**2
varianciam3 = proailidades_sucesso_receitam3 * \
    (receita_liquidam3-receita_esperada3)**2

varianciam1 = np.sum(varianciam1)
varianciam2 = np.sum(varianciam2)
varianciam3 = np.sum(varianciam3)
print("Variância mês 1:", varianciam1)
print("Variância mês 2:", varianciam2)
print("Variância mês 3:", varianciam3)

# desvio padrão do vpl esperado de cada contribuição do fluxo de caixa
desvio_padraom0 = np.sqrt(varianciam0)
desvio_padraom1 = np.sqrt(varianciam1)
desvio_padraom2 = np.sqrt(varianciam2)
desvio_padraom3 = np.sqrt(varianciam3)

print("Desvio padrão mês 0:", desvio_padraom0)
print("Desvio padrão mês 1:", desvio_padraom1)
print("Desvio padrão mês 2:", desvio_padraom2)
print("Desvio padrão mês 3:", desvio_padraom3)


# probabilidade de inviabilidade de um empreendimento (SUBSTITUINDO OS VALORES)
probabilidade_inviabilidade = varianciam0 + \
    (varianciam1/(1+tmr)**2) + (varianciam2/(1+tmr)**4) + (varianciam3/(1+tmr)**6)
print("Probabilidade de Inviabilidade:", probabilidade_inviabilidade)

# cALCULO DO DESVIO PADRAO DO VPL ESPERADO
desvio_padrao_vpl_esperado = np.sqrt(probabilidade_inviabilidade)
print("Desvio padrão do VPL Esperado:", desvio_padrao_vpl_esperado)

# CALCULAR Z
z = (0 - vpl_esperado)/desvio_padrao_vpl_esperado
print("Z:", z)

# CALCULAR A area abaixo da curva normal
area = norm.cdf(z)
print("Area abaixo da curva normal:", area)

# converter a area em porcentagem
area = area*100
print("probabilidade de inviabilidade:(%)", area)

# GRAFICO
# Defina os valores
vpl_esperado = 0  # valor presente líquido esperado (média)
desvio_padrao_vpl_esperado = 1  # desvio padrão do valor presente líquido esperado

# Crie um espaço de valores de vpl
vpl = np.linspace(-5, 5, 1000)

# Calcule a densidade de probabilidade para cada vpl
densidade = norm.pdf(vpl, vpl_esperado, desvio_padrao_vpl_esperado)

# Plote a curva normal
plt.figure(figsize=(10, 6))
plt.plot(vpl, densidade, label='Curva Normal', color='blue')

# Área abaixo da curva normal
z = -1.5  # valor de z para a área abaixo da curva
area = norm.cdf(z)
plt.fill_between(vpl, 0, densidade, where=(vpl < z), color='red',
                 alpha=0.5, label='probabilidade de inviabilidade')

# Área negativa da curva
plt.fill_between(vpl, 0, densidade, where=(vpl < 0), color='yellow',
                 alpha=0.5, label='Área total de inviabilidade')

# Linha vertical para o vpl esperado
plt.axvline(vpl_esperado, color='green', linestyle='--', label='VPL Esperado')

# Adicione o valor de z ao gráfico
plt.axvline(z, color='black', linestyle='--', label=f'z = {z:.2f}')

# Configurações do gráfico
plt.title('Distribuição Normal do VPL')
plt.xlabel('VPL')
plt.ylabel('Densidade de Probabilidade')
plt.legend()
plt.grid(True)

plt.show()
