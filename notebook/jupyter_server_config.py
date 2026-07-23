c = get_config()

# Notebook clásico (Notebook 6.x / notebook.notebookapp)
c.NotebookApp.nbserver_extensions = {
    "metrics_bridge": True,
}

# jupyter_server >=1.x (usado por nbclassic)
c.ServerApp.jpserver_extensions = {
    "metrics_bridge": True,
}