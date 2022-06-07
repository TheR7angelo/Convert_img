from script_svg_xaml import svg2xaml


if __name__ == '__main__':
    convert = svg2xaml()


    print("svg to xaml")
    print("Ou je doit sauvegarder ?")
    idx_dir = input("\t1.Dans le même dossier\n\t2.Dans un autre dossier\n")

    print("Mode dossier ou fichier ?")
    idx_mode = input("\t1.Dossier\n\t2.Fichier\n")

    if idx_mode == "2":
        path_dir = input("Quelle est le fichier ?\n")
    else:
        path_dir = input("Quelle est le dossier ?\n")

    if idx_dir == "2":
        path_save = input("Quelle est le dossier de sauvegarde ?\n")
    else:
        path_save = None

    match idx_mode:
        case "1":
            convert.convertDirSave(directory=path_dir, save_directory=path_save)
        case "2":
            convert.convertFileSave(file=path_dir, save_directory=path_save)
        case "_":
            print("entrer incorect\n")
    convert.remove()

