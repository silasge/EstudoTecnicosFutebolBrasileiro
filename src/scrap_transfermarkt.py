from pathlib import Path
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup


def retorna_html(url, headers):
    """
    Faz uma requisição HTTP para a URL fornecida utilizando os headers especificados e retorna o conteúdo HTML parseado.

    Args:
        url (str): URL para a qual será feita a requisição.
        headers (dict): Cabeçalhos HTTP a serem enviados na requisição.

    Returns:
        BeautifulSoup: Objeto BeautifulSoup contendo o HTML parseado da resposta.

    Raises:
        HTTPError: Se a resposta da requisição indicar erro (status code >= 400).
    """
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    html = BeautifulSoup(response.content, "html.parser")
    return html


def retorna_tabela_classificacao(html):
    """
    Extrai e retorna a tabela de classificação de um documento HTML do Transfermarkt.

    A função busca a tabela de classificação no HTML, processa o cabeçalho e as linhas,
    incluindo informações extras como classificação (Libertadores, Sul-Americana, Rebaixamento),
    escudo do clube, link para a temporada, status e título da temporada passada.

    Retorna um DataFrame pandas com os dados estruturados.

    Args:
        html (bs4.BeautifulSoup): Objeto BeautifulSoup contendo o HTML da página.

    Returns:
        pandas.DataFrame: DataFrame com a tabela de classificação e informações adicionais dos clubes.
    """
    tabela = html.find("table", {"class": "items"})

    tabela_cabecalho = tabela.find("thead").find_all("th")

    # Cabeçalho
    itens_cabecalho = []

    for i in tabela_cabecalho:
        if i.find("span"):
            itens_cabecalho.append(i.find("span").get("title").upper())
        elif i.text == "#":
            itens_cabecalho.append("POSICAO")
        else:
            itens_cabecalho.append(i.text.upper())

    # Adicionando itens extras no cabeçalho
    itens_cabecalho.append("CLASSIFICACAO")
    itens_cabecalho.append("ESCUDO")
    itens_cabecalho.append("HREF")
    itens_cabecalho.append("STATUS_TEMPORADA_PASSADA")
    itens_cabecalho.append("TITULO_TEMPORADA_PASSADA")

    # Linhas
    tabela_linhas = tabela.find("tbody").find_all("tr")

    linhas_da_tabela = []
    for linha in tabela_linhas:
        itens = []
        itens_extras = []
        item_linha = linha.find_all("td")
        for i in item_linha:
            if i.text != "":
                itens.append(i.text.replace("\xa0", "").replace("\n", "").strip())

            # Informações extras
            ## Pegando classificações pelas cores
            if i.get("class") == ['rechts', 'hauptlink']:
                if i.has_attr("style"):
                    color_bkg = i.get("style")
                    if "#afd179" in color_bkg or "#c3dc9a" in color_bkg or "#c3dc3a" in color_bkg or "#d6eab6" in color_bkg:
                        itens_extras.append("libertadores")
                    elif "#a5cce9" in color_bkg:
                        itens_extras.append("sul-americana")
                    elif "#f8a7a3" in color_bkg or "#f8cfcd" in color_bkg:
                        itens_extras.append("rebaixamento")
                else:
                    itens_extras.append(None)
            ## Pegando href para a temporada do clube
            elif i.get("class") == ['no-border-links', 'hauptlink']:
                itens_extras.append(i.find("a").get("href"))
                if i.find("span"):
                    itens_extras.append(i.find("span").get("title"))
                else:
                    itens_extras.append(None)
                
                if i.find("img"):
                    itens_extras.append(i.find("img").get("title"))
                else:
                    itens_extras.append(None)
            ## Pegando escudos dos clubes
            elif i.get("class") == ['zentriert', 'no-border-rechts']:
                itens_extras.append(i.find("img").get("src"))
            # Pegando situação do clube na temporada passada
            elif i.get("class") == ["icons_sprite", "icon-aufsteiger"]:
                itens_extras.append(i.find("span").get("title"))

        linhas_da_tabela.append(itens+itens_extras)

    df = pd.DataFrame(linhas_da_tabela, columns=itens_cabecalho)
    sleep(2)
    return df


def retorna_url_tabela_jogo_a_jogo_completa(base_url, url_time, header):
    """
    Recupera a URL completa da tabela de jogos do Campeonato Brasileiro para um time específico no Transfermarkt.

    Esta função constrói a URL da página do time, obtém seu conteúdo HTML e busca o link correspondente à tabela completa de jogos do Campeonato Brasileiro. 

    Retorna a URL completa para essa tabela.

    Args:
        base_url (str): URL base do site Transfermarkt.
        url_time (str): Caminho relativo da URL para o time específico.
        header (dict): Cabeçalhos HTTP para a requisição.
    Returns:
        str: URL completa da tabela de jogos do Campeonato Brasileiro para o time.
    """
    url = base_url + url_time
    response = retorna_html(url=url, headers=header)
    a_tags = response.find_all("a", {"class": "tm-tab"})

    for a in a_tags:
        href = a.get("href")
        # Campeonato brasileiro
        if "/plus/1#BRA1" in href:
            url_jogo_a_jogo_completa = base_url + href
    return url_jogo_a_jogo_completa


def retorna_tabela_jogo_a_jogo(html, id_time):
    """
    Extrai e retorna uma tabela de jogos do Brasileirão Série A a partir de um objeto HTML.

    A função busca dentro do HTML fornecido a seção correspondente ao Brasileirão Série A,
    extrai os cabeçalhos da tabela e as linhas de dados, incluindo informações extras como
    links para rodada, times, treinador e jogo. 
    
    Retorna um DataFrame do pandas contendo todos os dados extraídos.
    Args:
        html (BeautifulSoup): Objeto BeautifulSoup representando o HTML da página a ser analisada.
    Returns:
        pandas.DataFrame: DataFrame contendo os dados dos jogos, com colunas para cada campo extraído,
        incluindo links relevantes.
    """
    boxes = html.find_all("div", {"class": "box"})
    itens_cabecalho = []
    linhas_da_tabela = []
    for b in boxes:
        a_tag = b.find("h2").find("a")
        # Brasileirão serie a
        if a_tag and a_tag.get("name") == "BRA1":
            # Cabeçalhos 
            cabecalho = b.find("thead").find_all("th")
            for c in cabecalho:
                itens_cabecalho.append(c.text.strip().upper())

            itens_cabecalho.append("HREF_RODADA")
            itens_cabecalho.append("HREF_TIME_DA_CASA")
            itens_cabecalho.append("HREF_TIME_VISITANTE")
            itens_cabecalho.append("HREF_TREINADOR")
            itens_cabecalho.append("HREF_JOGO")
            itens_cabecalho.append("ID_TIME")
            
            # Linhas
            tabela_linhas = b.find("tbody").find_all("tr")
            for linha in tabela_linhas:
                itens = []
                itens_extras = []
                item_linha = linha.find_all("td")
                for i in item_linha:
                    # Não vou precisar dos escudos aqui. Por isso a negativa.
                    if not i.get("class") == ["zentriert", "no-border-rechts"]:
                        if i.text:
                            itens.append(i.text.strip())
                        # Condição exclusiva para quando não há treinadores preenchidos
                        # naquela rodada. Nesse caso, o td não tem classe e deixamos a linha
                        # como nula
                        elif not i.get("class"):
                            itens.append(None)
                        
                        if i.find("a"):
                            itens_extras.append(i.find("a").get("href"))
                        # Mesma coisa da condição acima. Quando não tem treinador o td
                        # não tem classe e deixamos a linha como nula
                        elif not i.get("class"):
                            itens_extras.append(None)
                # [id_time] para identificar de qual time é a tabela que
                # está sendo carregada
                linhas_da_tabela.append(itens+itens_extras+[id_time])

    df = pd.DataFrame(data=linhas_da_tabela, columns=itens_cabecalho)
    sleep(2)
    return df



if __name__ == "__main__":
    USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"}
    BASE_URL = "https://www.transfermarkt.com.br"

    caminho_tabela_classificacao = Path("./dados/serie_a/tabela_classificacao")
    caminho_tabela_classificacao.mkdir(parents=True, exist_ok=True)

    caminho_tabela_jogo_a_jogo = Path("./dados/serie_a/tabela_jogo_a_jogo")
    caminho_tabela_jogo_a_jogo.mkdir(parents=True, exist_ok=True)

    # O id da season no transfermarkt é sempre ano-1. Ou seja, a season com id 2002 é do campeonato
    # brasileiro serie a de 2003. O id 2024 é o de 2025 e assim por diante.
    # Provavelmente foi feito assim para manter o padrão das temporadas europeias que pegam dois anos.
    seasons = list(range(2003, 2025))
    
    for season_id in seasons:
        print(f"Fazendo scrap da tabela de classificação da temporada {season_id+1}")
        TABELAS_URL = BASE_URL + f"/campeonato-brasileiro-serie-a/tabelle/wettbewerb/BRA1/saison_id/{season_id}"

        html = retorna_html(TABELAS_URL, headers=USER_AGENT)
        df_tabela_classificacao = retorna_tabela_classificacao(html)
        # No nome dos csvs estou identificando o ano do campeonato. Portanto, season_id+1
        df_tabela_classificacao.to_csv(caminho_tabela_classificacao / f"tabela_classificacao_{season_id+1}.csv", index=False)
        
        href_times = df_tabela_classificacao["HREF"].to_list()
        for href in href_times:
            href_time = retorna_url_tabela_jogo_a_jogo_completa(BASE_URL, href, USER_AGENT)
            id_time = href_time.split("/verein/")[1].split("/saison_id")[0]
            print(f"Fazendo scrap dos jogos do time {id_time} na temporada {season_id+1}")
            html_tabela_jogo_a_jogo = retorna_html(href_time, headers=USER_AGENT)
            df_tabela_jogo_a_jogo = retorna_tabela_jogo_a_jogo(html_tabela_jogo_a_jogo, id_time)
            df_tabela_jogo_a_jogo.to_csv(caminho_tabela_jogo_a_jogo / f"tabela_jogo_a_jogo_{id_time}_{season_id+1}.csv", index=False)
        print(f"Temporada {season_id+1} concluída")
