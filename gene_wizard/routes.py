# if you want to import a model you need to keep in under the db instance, because it won't know until then
# need to treat the rest of gene_wizard like a package 
from flask import Flask, render_template, send_from_directory, send_file, url_for, flash, redirect, request, Markup, jsonify
from gene_wizard import app, mysql

# use a custom agent of the Gprofiler API
from gprofiler import GProfiler
gp = GProfiler(
    user_agent='Genedalph', #thanks Uku
    return_dataframe=True, #return pandas dataframe or plain python structures    
)
# for the graphing to be sent
import math
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import pandas as pd

#because they are in the package now ya gotta have the dot before your own created objects

@app.route("/", methods=['GET', 'POST'])#root or homepage
@app.route("/home") 
def home():

    cursor1 = mysql.connect().cursor()
    
    cursor1.execute("SELECT lncRNA_name, cell_line FROM DEG_lncRNA_roster;")
    home_table = cursor1.fetchall()
    cursor1.close()

    if request.method == 'POST':
        #Fetch form data 
        DEG_lncRNA_roster = request.form 
        lncRNA_name = DEG_lncRNA_roster['lncRNA_name']
        # strip things to prevents SQL injection 
        lncRNA_name = lncRNA_name.replace(';','')
        lncRNA_name = lncRNA_name.replace('=','')
        lncRNA_name = lncRNA_name.replace('"','')

        # cell_line = DEG_lncRNA_roster['cell_line']

        #make a cursor to use 
        cursor = mysql.connect().cursor()
        # cursor.execute("SELECT e.ENSG_id, e.gene_symbol, e.baseMean, e.log2FoldChange, e.lfcSE, e.pvalue, e.stat, e.padj")
        # cursor.execute("FROM Expression e, DEG_lncRNA_roster d")
        # cursor.execute("WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = " + lncRNA_name + ";")
        try: 
            # expression data 
            cursor.execute("SELECT e.ENSG_id, e.gene_symbol, ROUND(e.baseMean, 3), ROUND(e.log2FoldChange, 3), ROUND(e.lfcSE, 3), ROUND(e.pvalue, 3) , ROUND(e.stat, 3), ROUND(e.padj, 3) FROM Expression e, DEG_lncRNA_roster d WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = '" + lncRNA_name + "';")
            expression_data = cursor.fetchall()

            # cloud genes down 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND e.log2FoldChange < 0;") 
            genes_down = cursor.fetchall()
            # query genes down regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND e.log2FoldChange < 0 AND e.padj < .3;") 
            GOSTgenes_down = cursor.fetchall()
            query_down = [i[0] for i in GOSTgenes_down]
            # seems like genes_down etc are very large even on the API side to handle
            # makina a stringent separate query can get the most graph possible 

            # cloud genes up regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND e.log2FoldChange > 0;") 
            genes_up = cursor.fetchall()
            # query genes up regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND e.log2FoldChange > 0 AND e.padj < .3;") 
            GOSTgenes_up = cursor.fetchall()
            # needs to be done before the cursor close
            # cursor object is not like a list at all 
            query_up=[i[0] for i in GOSTgenes_up]
           
        finally:
            cursor.close()
        # cursor.execute("SELECT * FROM DEG_lncRNA_roster WHERE lncRNA_name='" + lncRNA_name + "'")
            data = cursor.fetchall()
        # cursor.execute("INSERT INTO search2(lncRNA_name) VALUES(%s)", lncRNA_name)
        # .commit seems to be for inserting only
        
        if data is None:
            return "That lncRNA is not available in genedalf"
        else:
            #query the upregulated and downregulated genes 
            sources = ["GO:MF","GO:CC","GO:BP","KEGG","REAC","WP", "HP"]
            # tricky cursor needs to be put in a python list 

            # even after a stringent filters we are capped at 80   
            if len(query_down) > 70:
                query_down = query_down[:70]
            if len(query_up) > 70:
                query_up = query_up[:70]

            # Remove None type variables
            query_down = list(filter(None.__ne__, query_down))
            query_up = list(filter(None.__ne__, query_up))

            # GET dataframes of pathways 
            # getting assertion error if the query yeilds no results
            GOSTup = gp.profile(organism='hsapiens', query = query_up, sources = sources, no_evidences=False, user_threshold = .5) 
            GOSTdown = gp.profile(organism='hsapiens', query = query_down, sources = sources, no_evidences=False, user_threshold = .5) 
            # get lists for plotting 
            # 3 things GOids, -log(adjP), and terms
            xGOtermsUp = GOSTup.native.to_list()
            # remember that pval is already corrected and the bar is -log(padj)
            listPadjUp = GOSTup.p_value.to_list()
            yPadjUp = []
            for e in listPadjUp:
                yPadjUp.append(-math.log(e))
            GOtextUp = GOSTup.name.to_list()
            xGOtermsDown = GOSTdown.native.to_list()
            listPadjDown = GOSTdown.p_value.to_list()
            yPadjDown = []
            for i in listPadjDown:
                yPadjDown.append(-math.log(i))
            GOtextDown = GOSTdown.name.to_list()

            dynamic_title = "Top Significant Differentially Expressed functions after " + lncRNA_name + "'s knockdown"

            ## plotly time 
            traceUp = go.Bar(
                x=xGOtermsUp,
                y=yPadjUp,
                text=GOtextUp,
                name='Significantly Up Regulated Genes',
                marker=dict(color='rgb(158,202,225)',
                line=dict(
                    color='rgb(8,48,107)',
                    width=1.5,)
                    ),
                    opacity=0.6
                )
            traceDown = go.Bar(
                x=xGOtermsDown,
                y=yPadjDown,
                text=GOtextDown,
                name='Significantly Down Regulated Genes',
                marker=dict(color='rgb(214,39,40)',
                line=dict(
                    color='rgb(247,182,210)',
                    width=1.5,)
                    ),
                    opacity=0.6
                )
            # keep the meat in trace 0 

            # try to unify 
            data = [traceUp, traceDown]
            layout= go.Layout(
                title= dynamic_title,
                yaxis= dict(title = '-log(adjusted p-value)')
                )
            fig = go.Figure(data=data, layout=layout)
            div_holder = plot(fig, output_type='div',  filename='straight_bars')

            return render_template('newResults.html', expression_data=expression_data, lncRNA_name=lncRNA_name,  genes_down=genes_down, genes_up=genes_up, div_holder=Markup(div_holder))
            
        cursor.close()

    return render_template('home.html', home_table = home_table) 
    # that posts = posts bit allows the html to reference our data inside here 
    # also remember that flask checks for a folder called templates

# @app.route("/about") 
# def about():
#     return render_template('about.html', title = 'About')

@app.route('/gProfilerTest', methods=['GET', 'POST'])
def gProfilerTest():

    conn = mysql.connect()
    cursor = conn.cursor()
    try: 
        # cloud genes down 
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange < 0;") 
        genes_down = cursor.fetchall()
        # query genes down regulated 
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange < 0 AND e.padj < .3;") 
        GOSTgenes_down = cursor.fetchall()
        query_down = [i[0] for i in GOSTgenes_down]
        # seems like genes_down etc are very large even on the API side to handle
        # makina a stringent separate query can get the most graph possible 
        
        # cloud genes up regulated 
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange > 0;") 
        genes_up = cursor.fetchall()
        # query genes up regulated 
        cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = 'MANCR' AND e.log2FoldChange > 0 AND e.padj < .3;") 
        GOSTgenes_up = cursor.fetchall()
        # needs to be done before the cursor close
        # cursor object is not like a list at all 
        query_up=[i[0] for i in GOSTgenes_up]
        
    finally: 
        cursor.close()
    
    print(len(query_up))
    #query the upregulated and downregulated genes 
    sources = ["GO:MF","GO:CC","GO:BP","KEGG","REAC","WP", "HP"]
    # tricky cursor needs to be put in a python list 

    # even after a stringent filters we are capped at 80   
    if len(query_down) > 70:
        query_down = query_down[:70]
    if len(query_up) > 70:
        query_up = query_up[:70]

    # GET dataframes of pathways 
    GOSTup = gp.profile(organism='hsapiens', query = query_up, sources = sources, no_evidences=False, user_threshold = .5) 
    GOSTdown = gp.profile(organism='hsapiens', query = query_down, sources = sources, no_evidences=False, user_threshold = .5) 
    # get lists for plotting 
    # 3 things GOids, -log(adjP), and terms
    xGOtermsUp = GOSTup.native.to_list()
    # remember that pval is already corrected and the bar is -log(padj)
    listPadjUp = GOSTup.p_value.to_list()
    yPadjUp = []
    for e in listPadjUp:
        yPadjUp.append(-math.log(e))
    GOtextUp = GOSTup.name.to_list()
    xGOtermsDown = GOSTdown.native.to_list()
    listPadjDown = GOSTdown.p_value.to_list()
    yPadjDown = []
    for i in listPadjDown:
        yPadjDown.append(-math.log(i))
    GOtextDown = GOSTdown.name.to_list()

    ## plotly time 
    traceUp = go.Bar(
        x=xGOtermsUp,
        y=yPadjUp,
        text=GOtextUp,
        name='Significantly Up Regulated Genes',
        marker=dict(color='rgb(158,202,225)',
        line=dict(
            color='rgb(8,48,107)',
            width=1.5,)
            ),
            opacity=0.6
        )
    traceDown = go.Bar(
        x=xGOtermsDown,
        y=yPadjDown,
        text=GOtextDown,
        name='Significantly Down Regulated Genes',
        marker=dict(color='rgb(214,39,40)',
        line=dict(
            color='rgb(247,182,210)',
            width=1.5,)
            ),
            opacity=0.6
        )
    # keep the meat in trace 0 
    
    # try to unify 
    data = [traceUp, traceDown]
    layout= go.Layout(
        title='Significant Differentially Expressed functions after a lncRNA knockdown',
        yaxis=dict(title = '-log(adjusted p-value)')
        )
    fig = go.Figure(data=data, layout=layout)
    div_holder = plot(fig, output_type='div',  filename='straight_bars') 

       
    # since it is a dict cursor try sending the df as a dict or json
    return render_template('gProfilerTest.html', genes_down=genes_down, genes_up=genes_up, div_holder=Markup(div_holder)) #, jsonify(result={"status": 200})

@app.route("/report/<filename>")
def send_image(filename):
    # filename = url_for(filename)
    return send_file(filename, mimetype='image/png')
    # return send_from_directory("Data" , filename)

NAMES=["ruby","MIR29A","EPB41L4A-AS1","KB-1471A8.1", "RP11-973D8.4", "XLOC_029037","XLOC_014806","MIR17HG","XLOC_042889","XLOC_010347","RP11-734K2.4"]

@app.route('/autocomplete',methods=['GET'])
def autocomplete():
    search = request.args.get('autocomplete')
    app.logger.debug(search)
    
    query = [s for s in NAMES if str(search) in s]
    
    return jsonify(json_list=query) 