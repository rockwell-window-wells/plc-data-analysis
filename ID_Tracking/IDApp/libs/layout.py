KV = '''
<HomeScreen>:
    name: "homescreen"
    id: home_screen

    MDBoxLayout:
        orientation: "vertical"

        AnchorLayout:
            anchor_x: "center"
            anchor_y: "top"

            Image:
                id: titlelogo
                size_hint: None, None
                size: 500, 500
                source: "assets/RockwellTitleLogo.png"

        AnchorLayout:
            anchor_x: "center"
            anchor_y: "top"

            MDGridLayout:
                cols:2
                size_hint: (0.35, 0.35)

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        text: "English"
                        font_style: "Button"
                        elevation: 5
                        # pos_hint: {"top": 1, "right": 1.0}
                        # on_release: root.translate_en()

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        text: "Espa\u00F1ol"
                        font_style: "Button"
                        elevation: 5
                        pos_hint: {"top": 1, "right": 1.0}
                        # on_release: root.translate_esp()


<OperatorIDScreen>:
    name: "operatoridscreen"
    id: operator_id_screen
    # plotsingle: plotsingle
    # annotatevalues: annotatevalues
    # annotatelines: annotatelines
    # employeename: employeename
    # analysistitle: analysistitle

    MDBoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        MDFloatLayout:

            MDLabel:
                id: operatoreidtitle
                text: "Operator IDs"
                font_style: "H5"
                pos_hint: {"top": 1.375, "x": 0.01}

    AnchorLayout:
        anchor_x: "center"
        anchor_y: "center"

        MDGridLayout:
            rows: 2
            columns: 2
            size_hint: (0.8, 0.8)
            padding: 20
            spacing: 20

            AnchorLayout:
                anchor_x: "center"
                anchor_y: "center"

                MDRaisedButton:
                    id: addoperator
                    text: "Add Operator"
                    font_style: "Button"
                    # md_bg_color: app.theme_cls.accent_color
                    # pos_hint: {"top": 0.5, "right": 0.5}
                    elevation: 5
                    # on_release:
                        # root.show_select_operator_dialog()

            AnchorLayout:
                anchor_x: "center"
                anchor_y: "center"

                MDRaisedButton:
                    id: dummybutton
                    text: "Dummy Button"
                    font_style: "Button"
                    # md_bg_color: app.theme_cls.accent_color
                    # pos_hint: {"top": 0.5, "right": 0.5}
                    elevation: 5
                    # on_release:
                        # root.show_select_operator_dialog()

            AnchorLayout:
                anchor_x: "center"
                anchor_y: "center"

                MDRaisedButton:
                    id: dummybutton
                    text: "Dummy Button"
                    font_style: "Button"
                    # md_bg_color: app.theme_cls.accent_color
                    # pos_hint: {"top": 0.5, "right": 0.5}
                    elevation: 5
                    # on_release:
                        # root.show_select_operator_dialog()

<Check@MDCheckbox>:
    group: 'group'
    size_hint: None, None
    size: dp(48), dp(48)

<OperatorContent>:
    id: operatorcontent
    operatornumbertext: operatornumbertext
    singleoperatorcheck: singleoperatorcheck
    dayshiftcheck: dayshiftcheck
    swingshiftcheck: swingshiftcheck
    graveyardshiftcheck: graveyardshiftcheck
    alloperatorscheck: alloperatorscheck
    orientation: "vertical"
    spacing: 10
    padding: 10
    size_hint_y: None
    height: "240dp"

    MDBoxLayout:
        orientation: "horizontal"
        padding: 10
        spacing: 10

        Check:
            id: singleoperatorcheck
            active: True
            pos_hint: {'center_x': .5, 'center_y': .75}

        MDLabel:
            text: "Single Operator"

    MDBoxLayout:
        orientation: "horizontal"
        padding: 10
        spacing: 10

        Check:
            id: dayshiftcheck
            pos_hint: {'center_x': .5, 'center_y': .75}

        MDLabel:
            text: "Day Shift"

    MDBoxLayout:
        orientation: "horizontal"
        padding: 10
        spacing: 10

        Check:
            id: swingshiftcheck
            pos_hint: {'center_x': .5, 'center_y': .75}

        MDLabel:
            text: "Swing Shift"

    MDBoxLayout:
        orientation: "horizontal"
        padding: 10
        spacing: 10

        Check:
            id: graveyardshiftcheck
            pos_hint: {'center_x': .5, 'center_y': .75}

        MDLabel:
            text: "Graveyard Shift"

    MDBoxLayout:
        orientation: "horizontal"
        padding: 10
        spacing: 10

        Check:
            id: alloperatorscheck
            pos_hint: {'center_x': .5, 'center_y': .75}

        MDLabel:
            text: "All Operators"



    MDTextField:
        id: operatornumbertext
        hint_text: "Enter Operator Number"


<OperatorEvaluationScreen>:
    name: "operatorevaluationscreen"
    id: operator_evaluation_screen
    evaluationparameterlabel: evaluationparameterlabel

    MDBoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        MDFloatLayout:

            MDLabel:
                id: operatorevaluationtitle
                text: "Operator Evaluation"
                font_style: "H5"
                pos_hint: {"top": 1.375, "x": 0.01}

    MDBoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        AnchorLayout:
            anchor_x: "center"
            anchor_y: "center"

            MDGridLayout:
                rows: 6
                size_hint: (0.4, 0.4)
                padding: 20
                spacing: 50

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        id: getreport
                        text: "Select Operator"
                        font_style: "Button"
                        # md_bg_color: app.theme_cls.accent_color
                        # pos_hint: {"top": 0.5, "right": 0.5}
                        elevation: 5
                        on_release:
                            root.show_select_operator_dialog()

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        id: getreport
                        text: "Starting Date/Time"
                        font_style: "Button"
                        # md_bg_color: app.theme_cls.accent_color
                        # pos_hint: {"top": 0.5, "right": 0.5}
                        elevation: 5
                        on_release:
                            root.show_start_time_dialog()

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        id: getreport
                        text: "Ending Date/Time"
                        font_style: "Button"
                        # md_bg_color: app.theme_cls.accent_color
                        # pos_hint: {"top": 0.5, "right": 0.5}
                        elevation: 5
                        on_release:
                            root.show_end_time_dialog()

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDRaisedButton:
                        id: getreport
                        text: "Generate Report"
                        font_style: "Button"
                        md_bg_color: app.theme_cls.accent_color
                        # pos_hint: {"top": 0.5, "right": 0.5}
                        elevation: 5
                        on_press:
                            evaluationparameterlabel.text = "Generating Report..."
                        on_release:
                            root.get_operator_reports()
                            evaluationparameterlabel.text = ""

                AnchorLayout:
                    anchor_x: "center"
                    anchor_y: "center"

                    MDLabel:
                        id: evaluationparameterlabel
                        text: ""
                        halign: "center"


    MDFloatingActionButton:
        id: button
        icon: "information-variant"
        pos_hint: {"top": 0.85, "right": 0.9}
        on_release:
            root.show_evaluation_info_dialog()


<EquipmentIDScreen>:
    name: "equipmentidscreen"
    id: equipment_id_screen

    MDLabel:
        id: equipmentidscreenlabel
        text: "This is the equipment ID screen"
        font_style: "H5"
        # pos_hint: {"top": 0.6, "x": 0.01}


<SettingsScreen>:
    name: "settings"
    # datafolderlabel: datafolderlabel
    # exportfolderlabel: exportfolderlabel

    MDLabel:
        id: settingstitle
        text: "This is the settings page"
        font_style: "H5"
        pos_hint: {"top": 0.75, "x": 0.01}

    # MDBoxLayout:
    #     orientation: "vertical"
    #     padding: 10
    #     spacing: 10
    #
    #     MDFloatLayout:
    #
    #         MDLabel:
    #             id: settingstitle
    #             text: app.settings_title
    #             font_style: "H5"
    #             pos_hint: {"top": 0.75, "x": 0.01}
    #
    #     MDBoxLayout:
    #         orientation: "horizontal"
    #         padding: [10]
    #         spacing: 10
    #
    #         MDTextField:
    #             id: datafolderpath
    #             hint_text: app.data_folder_label
    #             pos_hint: {"bottom": 0.35}
    #
    #         MDRaisedButton:
    #             text: app.set_btn_label
    #             font_style: "Button"
    #             elevation: 5
    #             pos_hint: {"bottom": 0.35}
    #             on_release:
    #                 root.set_datafolder(datafolderpath.text) if datafolderpath.text != "" else None
    #                 datafolderpath.text = ""
    #
    #         MDRectangleFlatButton:
    #             text: app.reset_btn_label
    #             font_style: "Button"
    #             elevation: 5
    #             pos_hint: {"bottom": 0.35}
    #             on_release: root.reset_datafolder()
    #
    #     MDLabel:
    #         id: datafolderlabel
    #         text: ""
    #         halign: "center"
    #
    #     MDBoxLayout:
    #         orientation: "horizontal"
    #         padding: [10]
    #         spacing: 10
    #
    #         MDTextField:
    #             id: exportfolderpath
    #             hint_text: app.export_folder_label
    #             pos_hint: {"top": 0.75}
    #
    #         MDRaisedButton:
    #             text: app.set_btn_label
    #             font_style: "Button"
    #             elevation: 5
    #             pos_hint: {"top": 0.75}
    #             on_release:
    #                 root.set_exportfolder(exportfolderpath.text) if exportfolderpath.text != "" else None
    #                 exportfolderpath.text = ""
    #
    #         MDRectangleFlatButton:
    #             text: app.reset_btn_label
    #             font_style: "Button"
    #             elevation: 5
    #             pos_hint: {"top": 0.75}
    #             on_release: root.reset_exportfolder(app.exportfolder_default)
    #
    #     MDLabel:
    #         id: exportfolderlabel
    #         text: ""
    #         halign: "center"


# Menu item in the DrawerList list.
<ItemDrawer>:
    theme_text_color: "Custom"

    IconLeftWidget:
        id: icon
        icon: root.icon
        theme_text_color: "Custom"
        text_color: root.text_color


<ContentNavigationDrawer>:
    orientation: "vertical"
    padding: "8dp"
    spacing: "8dp"

    AnchorLayout:
        anchor_x: "left"
        size_hint_y: None
        height: avatar.height

        Image:
            id: avatar
            size_hint: None, None
            size: 200, 50
            source: "assets/RockwellFullLogo.png"

    ScrollView:

        DrawerList:
            id: md_list

            ItemDrawer:
                text: "Home"
                icon: "home"
                on_release:
                    root.nav_drawer.set_state("close")
                    root.screen_manager.current = "homescreen"

            ItemDrawer:
                text: "Operator ID"
                icon: "account"
                on_release:
                    root.nav_drawer.set_state("close")
                    root.screen_manager.current = "operatoridscreen"

            ItemDrawer:
                text: "Operator Evaluation"
                icon: "chart-box"
                on_release:
                    root.nav_drawer.set_state("close")
                    root.screen_manager.current = "operatorevaluationscreen"

            ItemDrawer:
                text: "Equipment ID"
                icon: "tools"
                on_release:
                    root.nav_drawer.set_state("close")
                    root.screen_manager.current = "equipmentidscreen"

            ItemDrawer:
                text: "Settings"
                icon: "cog"
                on_release:
                    root.nav_drawer.set_state("close")
                    root.screen_manager.current = "settings"


RootScreen:
    id: root_screen

    MDToolbar:
        id: toolbar
        pos_hint: {"top": 1}
        elevation: 10
        title: "Navigation"
        left_action_items: [['menu', lambda x: nav_drawer.set_state("open")]]


    MDNavigationLayout:
        id: navigation_layout

        ScreenManager:
            id: screen_manager

            HomeScreen:

            OperatorIDScreen:

            OperatorEvaluationScreen:

            EquipmentIDScreen:

            SettingsScreen:


        MDNavigationDrawer:
            id: nav_drawer

            ContentNavigationDrawer:
                id: content_drawer
                screen_manager: screen_manager
                nav_drawer: nav_drawer



'''
