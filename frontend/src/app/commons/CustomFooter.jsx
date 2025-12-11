import {
    AppBar,
    Container,
    Toolbar,
    Typography,
} from "../../../node_modules/@mui/material";

import general from "../assets/images/logo_color.png";
import {useTranslation} from '../../../node_modules/react-i18next';
import React from "react";

function CustomFooter() {
    const {t} = useTranslation();
    return (
        <Container color="secondary">
            <AppBar color="secondary" sx={{position: "fixed", top: "auto", bottom: 0}}>
                <Toolbar sx={{justifyContent: "center"}}>
                    <img src={general} height={30} alt="MSU Manager" />
                    <Typography sx={{marginLeft: 1}}>{t('home.copyright')}</Typography>
                </Toolbar >
            </AppBar>
        </Container >
    );
}

export default CustomFooter;
