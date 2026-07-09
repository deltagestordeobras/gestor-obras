import unicodedata

import pandas as pd


COLUNA_MACROETAPA = "Macroetapa"
COLUNA_SERVICO = "Serviço"
COLUNA_MATERIAL = "Material"
COLUNA_CATEGORIA = "Categoria"
COLUNA_TIPO = "Tipo"
COLUNA_UNIDADE = "Unidade"
COLUNA_BASE = "Base"
COLUNA_COEFICIENTE = "Coeficiente"
COLUNA_PERDA = "Perda"
COLUNA_QUANTIDADE = "Quantidade"
COLUNA_OBSERVACAO = "Observação"

BASE_POR_QUANTIDADE = "por_quantidade"
BASE_POR_M2_OBRA = "por_m2_obra"
BASE_FIXO_OBRA = "fixo_obra"

TIPO_ESTRUTURAL = "material estrutural"
TIPO_AUXILIAR = "material auxiliar"
TIPO_CONSUMIVEL = "consumível"
TIPO_ACABAMENTO = "acabamento"
TIPO_EQUIPAMENTO = "equipamento"
TIPO_LOUCA_METAL = "louça e metal"
TIPO_ESQUADRIA = "esquadria"

MACRO_INFRAESTRUTURA = "Infraestrutura e Fundação"
MACRO_ESTRUTURA = "Estrutura"
MACRO_ALVENARIA = "Alvenaria"
MACRO_COBERTURA = "Cobertura"
MACRO_ELETRICA = "Instalações Elétricas"
MACRO_HIDRAULICA = "Instalações Hidráulicas"
MACRO_REVESTIMENTOS = "Revestimentos"
MACRO_PINTURA = "Pintura"
MACRO_ESQUADRIAS = "Esquadrias e Ferragens"
MACRO_LOUCAS = "Louças e Metais"

COLUNAS_COMPOSICAO_DETALHADA = [
    COLUNA_MACROETAPA,
    COLUNA_SERVICO,
    COLUNA_MATERIAL,
    COLUNA_CATEGORIA,
    COLUNA_TIPO,
    COLUNA_UNIDADE,
    COLUNA_BASE,
    COLUNA_COEFICIENTE,
    COLUNA_PERDA,
    COLUNA_OBSERVACAO,
]


def _item(
    macroetapa,
    servico,
    material,
    categoria,
    tipo,
    unidade,
    coeficiente,
    base=BASE_POR_QUANTIDADE,
    perda=0.0,
    observacao="",
):
    return {
        COLUNA_MACROETAPA: macroetapa,
        COLUNA_SERVICO: servico,
        COLUNA_MATERIAL: material,
        COLUNA_CATEGORIA: categoria,
        COLUNA_TIPO: tipo,
        COLUNA_UNIDADE: unidade,
        COLUNA_BASE: base,
        COLUNA_COEFICIENTE: coeficiente,
        COLUNA_PERDA: perda,
        COLUNA_OBSERVACAO: observacao,
    }


COMPOSICOES_DETALHADAS = [
    # 1. Infraestrutura e Fundação
    _item(MACRO_INFRAESTRUTURA, "Concreto Fundação", "Cimento CP II 50kg", "Concreto", TIPO_ESTRUTURAL, "sc", 7.2, perda=0.03, observacao="Consumo médio por m³ de concreto dosado em obra."),
    _item(MACRO_INFRAESTRUTURA, "Concreto Fundação", "Areia grossa", "Concreto", TIPO_ESTRUTURAL, "m3", 0.55, perda=0.05),
    _item(MACRO_INFRAESTRUTURA, "Concreto Fundação", "Brita 1", "Concreto", TIPO_ESTRUTURAL, "m3", 0.45, perda=0.05),
    _item(MACRO_INFRAESTRUTURA, "Concreto Fundação", "Brita 2", "Concreto", TIPO_ESTRUTURAL, "m3", 0.35, perda=0.05),
    _item(MACRO_INFRAESTRUTURA, "Concreto Fundação", "Aditivo plastificante", "Concreto", TIPO_AUXILIAR, "l", 0.80, perda=0.03),
    _item(MACRO_INFRAESTRUTURA, "Armação Fundação", "Aço CA50 10mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.45, perda=0.07, observacao="Coeficiente sobre peso total de aço da fundação."),
    _item(MACRO_INFRAESTRUTURA, "Armação Fundação", "Aço CA50 8mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.35, perda=0.07),
    _item(MACRO_INFRAESTRUTURA, "Armação Fundação", "Aço CA60 5mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.20, perda=0.08),
    _item(MACRO_INFRAESTRUTURA, "Armação Fundação", "Arame recozido 18", "Armação", TIPO_AUXILIAR, "kg", 0.025, perda=0.05),
    _item(MACRO_INFRAESTRUTURA, "Forma Fundação", "Madeira forma pinus", "Formas", TIPO_AUXILIAR, "m2", 1.00, perda=0.12),
    _item(MACRO_INFRAESTRUTURA, "Forma Fundação", "Sarrafo 5x2cm", "Formas", TIPO_AUXILIAR, "m", 1.80, perda=0.10),
    _item(MACRO_INFRAESTRUTURA, "Forma Fundação", "Prego 18x27", "Formas", TIPO_CONSUMIVEL, "kg", 0.10, perda=0.05),
    _item(MACRO_INFRAESTRUTURA, "Impermeabilização Baldrame", "Impermeabilizante asfáltico", "Impermeabilização", TIPO_AUXILIAR, "kg", 1.20, perda=0.08),
    _item(MACRO_INFRAESTRUTURA, "Impermeabilização Baldrame", "Argamassa polimérica", "Impermeabilização", TIPO_AUXILIAR, "kg", 3.00, perda=0.08),

    # 2. Estrutura
    _item(MACRO_ESTRUTURA, "Concreto Estrutural", "Cimento CP II 50kg", "Concreto", TIPO_ESTRUTURAL, "sc", 7.5, perda=0.03),
    _item(MACRO_ESTRUTURA, "Concreto Estrutural", "Areia média", "Concreto", TIPO_ESTRUTURAL, "m3", 0.52, perda=0.05),
    _item(MACRO_ESTRUTURA, "Concreto Estrutural", "Brita 1", "Concreto", TIPO_ESTRUTURAL, "m3", 0.78, perda=0.05),
    _item(MACRO_ESTRUTURA, "Concreto Estrutural", "Aditivo plastificante", "Concreto", TIPO_AUXILIAR, "l", 0.80, perda=0.03),
    _item(MACRO_ESTRUTURA, "Armação Estrutural", "Aço CA50 10mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.40, perda=0.07),
    _item(MACRO_ESTRUTURA, "Armação Estrutural", "Aço CA50 8mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.25, perda=0.07),
    _item(MACRO_ESTRUTURA, "Armação Estrutural", "Aço CA50 6.3mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.15, perda=0.08),
    _item(MACRO_ESTRUTURA, "Armação Estrutural", "Aço CA60 5mm", "Armação", TIPO_ESTRUTURAL, "kg", 0.20, perda=0.08),
    _item(MACRO_ESTRUTURA, "Armação Estrutural", "Arame recozido 18", "Armação", TIPO_AUXILIAR, "kg", 0.025, perda=0.05),
    _item(MACRO_ESTRUTURA, "Forma Estrutural", "Chapa compensada resinada", "Formas", TIPO_AUXILIAR, "m2", 1.00, perda=0.10),
    _item(MACRO_ESTRUTURA, "Forma Estrutural", "Sarrafo 5x2cm", "Formas", TIPO_AUXILIAR, "m", 2.00, perda=0.10),
    _item(MACRO_ESTRUTURA, "Forma Estrutural", "Pontalete madeira", "Formas", TIPO_AUXILIAR, "m", 1.20, perda=0.10),
    _item(MACRO_ESTRUTURA, "Forma Estrutural", "Prego 18x27", "Formas", TIPO_CONSUMIVEL, "kg", 0.12, perda=0.05),
    _item(MACRO_ESTRUTURA, "Laje", "Concreto usinado fck 25MPa", "Laje", TIPO_ESTRUTURAL, "m3", 0.10, perda=0.03),
    _item(MACRO_ESTRUTURA, "Laje", "Tela soldada Q92", "Laje", TIPO_ESTRUTURAL, "m2", 1.05, perda=0.05),
    _item(MACRO_ESTRUTURA, "Laje", "Escora metálica", "Laje", TIPO_AUXILIAR, "un", 0.35, perda=0.00),

    # 3. Alvenaria
    _item(MACRO_ALVENARIA, "Alvenaria Cerâmica", "Tijolo cerâmico 9x19x29", "Alvenaria", TIPO_ESTRUTURAL, "un", 18.0, perda=0.08),
    _item(MACRO_ALVENARIA, "Alvenaria Cerâmica", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.10, perda=0.05),
    _item(MACRO_ALVENARIA, "Alvenaria Cerâmica", "Areia média", "Argamassa", TIPO_AUXILIAR, "m3", 0.018, perda=0.08),
    _item(MACRO_ALVENARIA, "Alvenaria Cerâmica", "Cal hidratada", "Argamassa", TIPO_AUXILIAR, "sc", 0.030, perda=0.05),
    _item(MACRO_ALVENARIA, "Alvenaria Bloco Concreto", "Bloco concreto 14x19x39", "Alvenaria", TIPO_ESTRUTURAL, "un", 12.5, perda=0.06),
    _item(MACRO_ALVENARIA, "Alvenaria Bloco Concreto", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.08, perda=0.05),
    _item(MACRO_ALVENARIA, "Alvenaria Bloco Concreto", "Areia média", "Argamassa", TIPO_AUXILIAR, "m3", 0.015, perda=0.08),
    _item(MACRO_ALVENARIA, "Vergas e Contravergas", "Canaleta cerâmica", "Alvenaria", TIPO_ESTRUTURAL, "un", 2.6, perda=0.06),
    _item(MACRO_ALVENARIA, "Vergas e Contravergas", "Aço CA50 8mm", "Armação", TIPO_ESTRUTURAL, "kg", 1.10, perda=0.07),
    _item(MACRO_ALVENARIA, "Vergas e Contravergas", "Concreto usinado fck 20MPa", "Concreto", TIPO_ESTRUTURAL, "m3", 0.020, perda=0.03),

    # 4. Cobertura
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Estrutura metálica", "Cobertura", TIPO_ESTRUTURAL, "kg", 8.0, perda=0.05, observacao="Consumo por m² de cobertura simples residencial."),
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Telha metálica trapezoidal", "Cobertura", TIPO_ESTRUTURAL, "m2", 1.05, perda=0.05),
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Parafuso autobrocante com vedação", "Cobertura", TIPO_CONSUMIVEL, "un", 6.0, perda=0.05),
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Manta térmica aluminizada", "Cobertura", TIPO_AUXILIAR, "m2", 1.05, perda=0.08),
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Rufo galvanizado", "Cobertura", TIPO_AUXILIAR, "m", 0.25, perda=0.08),
    _item(MACRO_COBERTURA, "Cobertura Metálica", "Calha galvanizada", "Cobertura", TIPO_AUXILIAR, "m", 0.18, perda=0.08),
    _item(MACRO_COBERTURA, "Cobertura Cerâmica", "Telha cerâmica", "Cobertura", TIPO_ESTRUTURAL, "un", 16.0, perda=0.08),
    _item(MACRO_COBERTURA, "Cobertura Cerâmica", "Madeira cambará aparelhada", "Cobertura", TIPO_ESTRUTURAL, "m3", 0.035, perda=0.08),
    _item(MACRO_COBERTURA, "Cobertura Cerâmica", "Prego telheiro", "Cobertura", TIPO_CONSUMIVEL, "kg", 0.04, perda=0.05),
    _item(MACRO_COBERTURA, "Cobertura Sanduíche", "Telha sanduíche termoacústica", "Cobertura", TIPO_ESTRUTURAL, "m2", 1.05, perda=0.05),
    _item(MACRO_COBERTURA, "Cobertura Sanduíche", "Estrutura metálica", "Cobertura", TIPO_ESTRUTURAL, "kg", 6.0, perda=0.05),
    _item(MACRO_COBERTURA, "Cobertura Sanduíche", "Parafuso autobrocante com vedação", "Cobertura", TIPO_CONSUMIVEL, "un", 6.0, perda=0.05),

    # 5. Instalações Elétricas
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Eletroduto corrugado 20mm", "Elétrica", TIPO_AUXILIAR, "m", 1.40, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Eletroduto corrugado 25mm", "Elétrica", TIPO_AUXILIAR, "m", 0.35, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Cabo flexível 1.5mm²", "Elétrica", TIPO_AUXILIAR, "m", 2.2, base=BASE_POR_M2_OBRA, perda=0.10),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Cabo flexível 2.5mm²", "Elétrica", TIPO_AUXILIAR, "m", 3.8, base=BASE_POR_M2_OBRA, perda=0.10),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Cabo flexível 4mm²", "Elétrica", TIPO_AUXILIAR, "m", 0.9, base=BASE_POR_M2_OBRA, perda=0.10),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Cabo flexível 6mm²", "Elétrica", TIPO_AUXILIAR, "m", 0.35, base=BASE_POR_M2_OBRA, perda=0.10),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Quadro de distribuição QDC", "Elétrica", TIPO_EQUIPAMENTO, "un", 1.0, base=BASE_FIXO_OBRA, perda=0.00),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Disjuntor monopolar", "Elétrica", TIPO_EQUIPAMENTO, "un", 0.12, base=BASE_POR_M2_OBRA, perda=0.00),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Disjuntor bipolar", "Elétrica", TIPO_EQUIPAMENTO, "un", 0.025, base=BASE_POR_M2_OBRA, perda=0.00),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "DR residual", "Elétrica", TIPO_EQUIPAMENTO, "un", 1.0, base=BASE_FIXO_OBRA, perda=0.00),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Caixa 4x2", "Elétrica", TIPO_AUXILIAR, "un", 0.42, base=BASE_POR_M2_OBRA, perda=0.05),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Caixa 4x4", "Elétrica", TIPO_AUXILIAR, "un", 0.08, base=BASE_POR_M2_OBRA, perda=0.05),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Tomada 10A", "Elétrica", TIPO_EQUIPAMENTO, "un", 0.20, base=BASE_POR_M2_OBRA, perda=0.03),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Interruptor simples", "Elétrica", TIPO_EQUIPAMENTO, "un", 0.10, base=BASE_POR_M2_OBRA, perda=0.03),
    _item(MACRO_ELETRICA, "Instalação Elétrica", "Fita isolante", "Elétrica", TIPO_CONSUMIVEL, "un", 0.03, base=BASE_POR_M2_OBRA, perda=0.05),

    # 6. Instalações Hidráulicas
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Tubo PVC soldável 25mm", "Hidráulica", TIPO_AUXILIAR, "m", 0.55, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Tubo PVC soldável 32mm", "Hidráulica", TIPO_AUXILIAR, "m", 0.18, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Tubo PVC esgoto 40mm", "Hidráulica", TIPO_AUXILIAR, "m", 0.18, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Tubo PVC esgoto 50mm", "Hidráulica", TIPO_AUXILIAR, "m", 0.22, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Tubo PVC esgoto 100mm", "Hidráulica", TIPO_AUXILIAR, "m", 0.16, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Conexões PVC soldável", "Hidráulica", TIPO_AUXILIAR, "un", 0.65, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Conexões PVC esgoto", "Hidráulica", TIPO_AUXILIAR, "un", 0.45, base=BASE_POR_M2_OBRA, perda=0.08),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Registro gaveta", "Hidráulica", TIPO_EQUIPAMENTO, "un", 0.04, base=BASE_POR_M2_OBRA, perda=0.00),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Registro pressão", "Hidráulica", TIPO_EQUIPAMENTO, "un", 0.03, base=BASE_POR_M2_OBRA, perda=0.00),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Caixa gordura", "Hidráulica", TIPO_EQUIPAMENTO, "un", 1.0, base=BASE_FIXO_OBRA, perda=0.00),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Caixa inspeção", "Hidráulica", TIPO_EQUIPAMENTO, "un", 2.0, base=BASE_FIXO_OBRA, perda=0.00),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Ralo sifonado", "Hidráulica", TIPO_EQUIPAMENTO, "un", 0.04, base=BASE_POR_M2_OBRA, perda=0.00),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Cola PVC", "Hidráulica", TIPO_CONSUMIVEL, "un", 0.025, base=BASE_POR_M2_OBRA, perda=0.05),
    _item(MACRO_HIDRAULICA, "Instalação Hidráulica", "Fita veda rosca", "Hidráulica", TIPO_CONSUMIVEL, "un", 0.020, base=BASE_POR_M2_OBRA, perda=0.05),

    # 7. Revestimentos
    _item(MACRO_REVESTIMENTOS, "Chapisco", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.08, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Chapisco", "Areia grossa", "Argamassa", TIPO_AUXILIAR, "m3", 0.015, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Reboco Interno", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.10, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Reboco Interno", "Areia média", "Argamassa", TIPO_AUXILIAR, "m3", 0.018, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Reboco Interno", "Cal hidratada", "Argamassa", TIPO_AUXILIAR, "sc", 0.030, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Reboco Externo", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.12, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Reboco Externo", "Areia média", "Argamassa", TIPO_AUXILIAR, "m3", 0.020, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Reboco Externo", "Cal hidratada", "Argamassa", TIPO_AUXILIAR, "sc", 0.030, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Contrapiso", "Cimento CP II 50kg", "Argamassa", TIPO_AUXILIAR, "sc", 0.16, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Contrapiso", "Areia média", "Argamassa", TIPO_AUXILIAR, "m3", 0.025, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Piso Cerâmico", "Cerâmica piso", "Acabamento", TIPO_ACABAMENTO, "m2", 1.05, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Piso Cerâmico", "Argamassa AC1", "Acabamento", TIPO_AUXILIAR, "sc", 0.22, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Piso Cerâmico", "Rejunte", "Acabamento", TIPO_AUXILIAR, "kg", 0.05, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Piso Porcelanato", "Porcelanato", "Acabamento", TIPO_ACABAMENTO, "m2", 1.05, perda=0.08),
    _item(MACRO_REVESTIMENTOS, "Piso Porcelanato", "Argamassa AC2", "Acabamento", TIPO_AUXILIAR, "sc", 0.25, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Piso Porcelanato", "Rejunte porcelanato", "Acabamento", TIPO_AUXILIAR, "kg", 0.05, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Revestimento Parede", "Cerâmica parede", "Acabamento", TIPO_ACABAMENTO, "m2", 1.05, perda=0.10),
    _item(MACRO_REVESTIMENTOS, "Revestimento Parede", "Argamassa AC2", "Acabamento", TIPO_AUXILIAR, "sc", 0.25, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Revestimento Parede", "Rejunte", "Acabamento", TIPO_AUXILIAR, "kg", 0.05, perda=0.05),
    _item(MACRO_REVESTIMENTOS, "Rodapé", "Rodapé cerâmico", "Acabamento", TIPO_ACABAMENTO, "m", 1.00, perda=0.08),

    # 8. Pintura
    _item(MACRO_PINTURA, "Pintura Interna", "Selador acrílico", "Pintura", TIPO_AUXILIAR, "l", 0.12, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Interna", "Massa corrida PVA", "Pintura", TIPO_AUXILIAR, "kg", 0.80, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Interna", "Tinta acrílica premium", "Pintura", TIPO_ACABAMENTO, "l", 0.18, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Interna", "Lixa parede", "Pintura", TIPO_CONSUMIVEL, "un", 0.25, perda=0.05),
    _item(MACRO_PINTURA, "Pintura Externa", "Selador acrílico externo", "Pintura", TIPO_AUXILIAR, "l", 0.14, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Externa", "Textura acrílica", "Pintura", TIPO_ACABAMENTO, "kg", 1.20, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Externa", "Tinta acrílica externa", "Pintura", TIPO_ACABAMENTO, "l", 0.20, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Esmalte", "Fundo preparador madeira/metal", "Pintura", TIPO_AUXILIAR, "l", 0.10, perda=0.08),
    _item(MACRO_PINTURA, "Pintura Esmalte", "Esmalte sintético", "Pintura", TIPO_ACABAMENTO, "l", 0.12, perda=0.08),

    # 9. Esquadrias e Ferragens
    _item(MACRO_ESQUADRIAS, "Portas Internas", "Porta interna semioca", "Esquadrias", TIPO_ESQUADRIA, "un", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Internas", "Batente madeira", "Esquadrias", TIPO_ESQUADRIA, "un", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Internas", "Guarnição madeira", "Esquadrias", TIPO_ESQUADRIA, "jogo", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Internas", "Fechadura interna", "Ferragens", TIPO_AUXILIAR, "un", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Internas", "Dobradiça 3\"", "Ferragens", TIPO_AUXILIAR, "un", 3.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Externas", "Porta externa maciça", "Esquadrias", TIPO_ESQUADRIA, "un", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Externas", "Fechadura externa", "Ferragens", TIPO_AUXILIAR, "un", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Portas Externas", "Dobradiça reforçada", "Ferragens", TIPO_AUXILIAR, "un", 3.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Janelas Alumínio", "Janela alumínio com vidro", "Esquadrias", TIPO_ESQUADRIA, "m2", 1.00, perda=0.00),
    _item(MACRO_ESQUADRIAS, "Janelas Alumínio", "Parafuso e bucha 8mm", "Ferragens", TIPO_CONSUMIVEL, "un", 8.00, perda=0.05),
    _item(MACRO_ESQUADRIAS, "Janelas Alumínio", "Silicone vedação", "Ferragens", TIPO_CONSUMIVEL, "un", 0.20, perda=0.05),
    _item(MACRO_ESQUADRIAS, "Vidro", "Vidro temperado 8mm", "Esquadrias", TIPO_ESQUADRIA, "m2", 1.00, perda=0.05),

    # 10. Louças e Metais
    _item(MACRO_LOUCAS, "Banheiro Completo", "Vaso sanitário com caixa acoplada", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Cuba lavatório", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Torneira lavatório", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Registro pressão chuveiro", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Registro gaveta banheiro", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Chuveiro elétrico", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Sifão lavatório", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Banheiro Completo", "Engate flexível", "Metais", TIPO_LOUCA_METAL, "un", 2.00, perda=0.00),
    _item(MACRO_LOUCAS, "Cozinha Completa", "Cuba inox cozinha", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Cozinha Completa", "Torneira cozinha", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Cozinha Completa", "Sifão cozinha", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Área Serviço", "Tanque louça/sintético", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Área Serviço", "Torneira tanque", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Vaso Sanitário", "Vaso sanitário com caixa acoplada", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Cuba", "Cuba lavatório", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Torneira", "Torneira lavatório", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Chuveiro", "Chuveiro elétrico", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Tanque", "Tanque louça/sintético", "Louças", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Sifão", "Sifão lavatório", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
    _item(MACRO_LOUCAS, "Engate Flexível", "Engate flexível", "Metais", TIPO_LOUCA_METAL, "un", 1.00, perda=0.00),
]


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _corrigir_mojibake(valor):
    texto = str(valor or "")

    for _ in range(3):
        try:
            corrigido = texto.encode("latin1").decode("utf-8")
        except UnicodeError:
            break

        if corrigido == texto:
            break

        texto = corrigido

    return texto


def _normalizar_texto(valor):
    texto = _corrigir_mojibake(valor)
    texto = texto.replace("²", "2").replace("³", "3")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = "".join(ch.lower() if ch.isalnum() else " " for ch in texto)

    return " ".join(texto.split())


def obter_composicoes_detalhadas():
    return pd.DataFrame(COMPOSICOES_DETALHADAS, columns=COLUNAS_COMPOSICAO_DETALHADA)


def obter_macroetapas():
    return [
        MACRO_INFRAESTRUTURA,
        MACRO_ESTRUTURA,
        MACRO_ALVENARIA,
        MACRO_COBERTURA,
        MACRO_ELETRICA,
        MACRO_HIDRAULICA,
        MACRO_REVESTIMENTOS,
        MACRO_PINTURA,
        MACRO_ESQUADRIAS,
        MACRO_LOUCAS,
    ]


def validar_composicoes_detalhadas(df_composicoes=None):
    composicoes = obter_composicoes_detalhadas() if df_composicoes is None else df_composicoes

    if composicoes is None or composicoes.empty:
        return False, "Biblioteca de composições detalhadas vazia"

    colunas_faltantes = [
        coluna for coluna in COLUNAS_COMPOSICAO_DETALHADA
        if coluna not in composicoes.columns
    ]

    if colunas_faltantes:
        return False, f"Colunas obrigatórias ausentes: {', '.join(colunas_faltantes)}"

    coeficientes = pd.to_numeric(
        composicoes[COLUNA_COEFICIENTE],
        errors="coerce",
    )

    if coeficientes.isna().any():
        return False, "Existem coeficientes inválidos nas composições detalhadas"

    return True, None


def obter_composicao_servico(servico, df_composicoes=None):
    composicoes = obter_composicoes_detalhadas() if df_composicoes is None else df_composicoes

    if composicoes is None or composicoes.empty:
        return pd.DataFrame(columns=COLUNAS_COMPOSICAO_DETALHADA)

    servico_normalizado = _normalizar_texto(servico)

    return composicoes[
        composicoes[COLUNA_SERVICO].apply(_normalizar_texto)
        == servico_normalizado
    ].copy()


def obter_composicoes_macroetapa(macroetapa, df_composicoes=None):
    composicoes = obter_composicoes_detalhadas() if df_composicoes is None else df_composicoes

    if composicoes is None or composicoes.empty:
        return pd.DataFrame(columns=COLUNAS_COMPOSICAO_DETALHADA)

    macroetapa_normalizada = _normalizar_texto(macroetapa)

    return composicoes[
        composicoes[COLUNA_MACROETAPA].apply(_normalizar_texto)
        == macroetapa_normalizada
    ].copy()


def calcular_materiais_servico(
    servico,
    quantidade=0,
    area_total=0,
    df_composicoes=None,
    aplicar_perdas=True,
):
    composicao = obter_composicao_servico(servico, df_composicoes)

    if composicao.empty:
        return pd.DataFrame(columns=COLUNAS_COMPOSICAO_DETALHADA + [COLUNA_QUANTIDADE])

    quantidade = _numero(quantidade)
    area_total = _numero(area_total)
    materiais = composicao.copy()

    def calcular_quantidade(row):
        coeficiente = _numero(row.get(COLUNA_COEFICIENTE))
        perda = _numero(row.get(COLUNA_PERDA)) if aplicar_perdas else 0.0
        base = row.get(COLUNA_BASE)

        if base == BASE_FIXO_OBRA:
            quantidade_base = 1.0
        elif base == BASE_POR_M2_OBRA:
            quantidade_base = area_total
        else:
            quantidade_base = quantidade

        return quantidade_base * coeficiente * (1 + perda)

    materiais[COLUNA_QUANTIDADE] = materiais.apply(calcular_quantidade, axis=1)

    return materiais


def calcular_materiais_por_quantitativos(
    quantitativos,
    area_total=0,
    df_composicoes=None,
    aplicar_perdas=True,
):
    if not quantitativos:
        return pd.DataFrame(columns=COLUNAS_COMPOSICAO_DETALHADA + [COLUNA_QUANTIDADE])

    lista_materiais = []

    for servico, quantidade in quantitativos.items():
        materiais_servico = calcular_materiais_servico(
            servico=servico,
            quantidade=quantidade,
            area_total=area_total,
            df_composicoes=df_composicoes,
            aplicar_perdas=aplicar_perdas,
        )

        if not materiais_servico.empty:
            lista_materiais.append(materiais_servico)

    if not lista_materiais:
        return pd.DataFrame(columns=COLUNAS_COMPOSICAO_DETALHADA + [COLUNA_QUANTIDADE])

    return pd.concat(lista_materiais, ignore_index=True)


def agrupar_materiais_detalhados(df_materiais):
    if df_materiais is None or df_materiais.empty:
        return pd.DataFrame(columns=[
            COLUNA_MACROETAPA,
            COLUNA_MATERIAL,
            COLUNA_CATEGORIA,
            COLUNA_TIPO,
            COLUNA_UNIDADE,
            COLUNA_QUANTIDADE,
        ])

    materiais = df_materiais.copy()

    if COLUNA_QUANTIDADE not in materiais.columns:
        materiais[COLUNA_QUANTIDADE] = 0

    materiais[COLUNA_QUANTIDADE] = pd.to_numeric(
        materiais[COLUNA_QUANTIDADE],
        errors="coerce",
    ).fillna(0)

    agrupadores = [
        COLUNA_MACROETAPA,
        COLUNA_MATERIAL,
        COLUNA_CATEGORIA,
        COLUNA_TIPO,
        COLUNA_UNIDADE,
    ]

    return (
        materiais
        .groupby(agrupadores, as_index=False)
        .agg({COLUNA_QUANTIDADE: "sum"})
        .sort_values([COLUNA_MACROETAPA, COLUNA_QUANTIDADE], ascending=[True, False])
    )


def gerar_biblioteca_para_orcamento(area_total=0, quantitativos=None, aplicar_perdas=True):
    quantitativos = quantitativos or {}

    return {
        "composicoes": obter_composicoes_detalhadas(),
        "materiais": calcular_materiais_por_quantitativos(
            quantitativos=quantitativos,
            area_total=area_total,
            aplicar_perdas=aplicar_perdas,
        ),
        "materiais_agrupados": agrupar_materiais_detalhados(
            calcular_materiais_por_quantitativos(
                quantitativos=quantitativos,
                area_total=area_total,
                aplicar_perdas=aplicar_perdas,
            )
        ),
        "macroetapas": obter_macroetapas(),
    }