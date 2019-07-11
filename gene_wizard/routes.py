# if you want to import a model you need to keep in under the db instance, because it won't know until then
# need to treat the rest of gene_wizard like a package 
from flask import Flask, render_template, send_from_directory, send_file, url_for, flash, redirect, request, Markup, jsonify
from gene_wizard import app, mysql
import os 

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

# big list for lncRNA autocomplete 
NAMES = ["DEANR1,H9","DNM3OS,SKOV3","Firre,Patski","FOXA2,H9","H19,HTR","HNF1A-AS1,EAC",
"IGFL2-AS1,MCF10A-AT1","lincDUSP,V481","lincDUSP,V703","MANCR,MDA-MB-231","PANCR,H9-Cardiomyocyte",
"SENCR,HCASMCs","AC016831.7,u87","CCAT1,hela","CTC-428G20.6,u87","CTC-428G20.6,hela","EPB41L4A-AS1,u87",
"EPB41L4A-AS1,k562","KB-1471A8.1,hela","LAMTOR5-AS1,hela","LINC00263,u87","LINC00263,k562",
"LINC00263,hela","LINC00680,u87","LINC00680,hela","LINC00909,u87","LINC00909,k562","MIR142,k562",
"MIR17HG,hela","MIR210HG,u87","MIR29A,u87","PVT1,u87","PVT1,hela","RP11-1094M14.11,u87",
"RP11-126L15.4,u87","RP11-734K2.4,u87","RP11-96L14.7,u87","RP11-973D8.4,u87","RP5-1148A21.3,hela",
"SNHG1,u87","SNHG12,u87","TRAM2-AS1,u87","XLOC_010347,u87","XLOC_014806,u87","XLOC_015111,u87",
"XLOC_026118,u87","XLOC_029037,u87","XLOC_040566,u87","XLOC_042889,k562","XLOC_051509,u87","XLOC_054068,u87"]

#because they are in the package now ya gotta have the dot before your own created objects

@app.route("/", methods=['GET', 'POST'])#root or homepage
def home():

    cursor1 = mysql.connect().cursor()
    
    cursor1.execute("SELECT lncRNA_name, cell_line FROM DEG_lncRNA_roster;")
    home_table = cursor1.fetchall()
    cursor1.close()

    if request.method == 'POST':
        #Fetch form data 
        DEG_lncRNA_roster = request.form 
        comma_sep = DEG_lncRNA_roster['comma_sep']
        # strip things to prevents SQL injection 
        comma_sep = comma_sep.replace(';','')
        comma_sep = comma_sep.replace('=','')
        comma_sep = comma_sep.replace('"','')

        try:
            lncRNA_name , cell_line = comma_sep.split(',', 1)
        except ValueError:
            return render_template("ValueError.html")
        
        #make a cursor to use to connect to mysql
        cursor = mysql.connect().cursor()
        
        try: 
            # expression data 
            cursor.execute("SELECT e.ENSG_id, e.gene_symbol, ROUND(e.baseMean, 3), ROUND(e.log2FoldChange, 3), ROUND(e.lfcSE, 3), ROUND(e.pvalue, 3) , ROUND(e.stat, 3), ROUND(e.padj, 3) FROM Expression e, DEG_lncRNA_roster d WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id and d.lncRNA_name = '" + lncRNA_name + "' and d.cell_line = '" + cell_line + "';")
            expression_data = cursor.fetchall()

            # cloud genes down 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND d.cell_line = '" + cell_line + "' AND e.log2FoldChange < 0;") 
            genes_down = cursor.fetchall()
            # query genes down regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND d.cell_line = '" + cell_line + "' AND e.log2FoldChange < 0 ORDER BY e.padj ASC;") 
            GOSTgenes_down = cursor.fetchall()
            query_down = [i[0] for i in GOSTgenes_down]
            # seems like genes_down etc are very large even on the API side to handle
            # makina a stringent separate query can get the most graph possible 

            # cloud genes up regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND d.cell_line = '" + cell_line + "' AND e.log2FoldChange > 0;") 
            genes_up = cursor.fetchall()
            # query genes up regulated 
            cursor.execute("SELECT DISTINCT e.gene_symbol FROM DEG_lncRNA_roster d, Expression e WHERE d.roster_id = e.DEG_lncRNA_roster_roster_id AND d.lncRNA_name = '" + lncRNA_name + "' AND d.cell_line = '" + cell_line + "' AND e.log2FoldChange > 0 ORDER BY e.padj ASC;") 
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
            return render_template("ValueError.html")
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
            # Get lists of DEG genes for plotting 
            # 3 main things things GOids, -log(adjP), and terms
            # remember that pval is already corrected and the bar is -log(padj)
            try:
                GOSTup = gp.profile(organism='hsapiens', query = query_up, sources = sources, no_evidences=False, user_threshold = .5) 
                xGOtermsUp = GOSTup.native.to_list()
                listPadjUp = GOSTup.p_value.to_list()
                yPadjUp = []
                for e in listPadjUp:
                    yPadjUp.append(-math.log(e))
                GOtextUp = GOSTup.name.to_list()
                # plotly for up regulated portion  
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

            except AssertionError:
                pass 
            try:
                GOSTdown = gp.profile(organism='hsapiens', query = query_down, sources = sources, no_evidences=False, user_threshold = .5) 
                xGOtermsDown = GOSTdown.native.to_list()
                listPadjDown = GOSTdown.p_value.to_list()
                yPadjDown = []
                for i in listPadjDown:
                    yPadjDown.append(-math.log(i))
                GOtextDown = GOSTdown.name.to_list()
                # plotly for down regulated portion 
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

            except AssertionError:
                pass
            
            dynamic_title = "Top Significant Differentially Expressed functions after " + lncRNA_name + "'s knockdown in the " + cell_line + " cell line"

            # try to unify both graphs into 1 Figure 
            # failsafe to ensure if one query is empty or yields no results 
            # It will try displaying other data. 
            try: 
                if traceDown is None:
                    data = traceUp
                elif traceUp is None:
                    data = traceDown
                else:
                    data = [traceUp, traceDown]
            except UnboundLocalError:
                return render_template("NoPathwaysError.html")
            
            layout= go.Layout(
                title= dynamic_title,
                yaxis= dict(title = '-log(adjusted p-value)')
                )
            fig = go.Figure(data=data, layout=layout)
            div_holder = plot(fig, output_type='div',  filename='straight_bars')

            return render_template('newResults.html', expression_data=expression_data, lncRNA_name=lncRNA_name, cell_line=cell_line, genes_down=genes_down, genes_up=genes_up, div_holder=Markup(div_holder))
            
        cursor.close()

    return render_template('home.html', home_table = home_table) 
    # that posts = posts bit allows the html to reference our data inside here 
    # also remember that flask checks for a folder called templates

@app.route("/about",  methods=['GET', 'POST']) 
def about():
    
    return render_template('about.html', title = 'About')


@app.route('/favicon')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'wizard.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/report/<filename>")
def send_image(filename):
    # filename = url_for(filename)
    return send_file(filename, mimetype='image/png')
    # return send_from_directory("Data" , filename)

@app.route('/autocomplete',methods=['GET'])
def autocomplete():
    # fetch the query from the front end 
    search = request.args.get('autocomplete')
    app.logger.debug(search)
    #see if there is anything like the initial query in our list 
    query = [s for s in NAMES if str(search) in s]
    
    return jsonify(json_list=query) 