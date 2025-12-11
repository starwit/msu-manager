import React from "react";
import {ThemeProvider} from "../../../../node_modules/@mui/material";
import general from "./general/ComponentTheme";

function MainTheme(props) {
    return (
        <ThemeProvider theme={general}>
            {props.children}
        </ThemeProvider>
    )
}

export default MainTheme;
