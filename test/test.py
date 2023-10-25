import sys
import cProfile
import pstats

sys.path.append('//tmddom01.lcl/spe/PROJECT OFFICE/99. Doc Control Transfer/26. Projetos Mateus/Project/Python/GRDEGPN/src/')
from director import Director

class Test():
    def __init__(self):
        self.director=Director()

    def select_and_set_folder_path(self):
        self.director=Director()
        self.director.folder_path()

    def process_files(self):
        self.director.GRD_EGPN_Validation()

if __name__=="__main__":
    test=Test()
    with cProfile.Profile() as profile:
        test.select_and_set_folder_path()
        test.process_files()

    with open("results.txt", "w") as f:
        stats = pstats.Stats(profile, stream=f)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.print_stats()
