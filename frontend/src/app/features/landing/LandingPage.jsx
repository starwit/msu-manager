import { useState } from "react";
import { Box, Tab, Typography } from "../../../../node_modules/@mui/material";
import { useTranslation } from "../../../../node_modules/react-i18next";
import TabContext from '@mui/lab/TabContext';
import TabList from '@mui/lab/TabList';
import PropTypes from 'prop-types';
import Status from "../status/Status";

export default function StartPage() {
    const { t, i18n } = useTranslation();

    const [value, setValue] = useState(0);

    function CustomTabPanel(props) {
        const { children, value, index, ...other } = props;

        return (
            <div
                role="tabpanel"
                hidden={value !== index}
                id={`simple-tabpanel-${index}`}
                aria-labelledby={`simple-tab-${index}`}
                {...other}
            >
                {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
            </div>
        );
    }

    CustomTabPanel.propTypes = {
        children: PropTypes.node,
        index: PropTypes.number.isRequired,
        value: PropTypes.number.isRequired,
    };

    function a11yProps(index) {
        return {
            id: `simple-tab-${index}`,
            'aria-controls': `simple-tabpanel-${index}`,
        };
    }

    function handleChange(event, newValue) {
        setValue(newValue);
    }

    return (
        <>
            <Box sx={{ width: '100%', typography: 'body1' }}>
                <TabContext value={value}>
                    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                        <TabList onChange={handleChange} aria-label="lab API tabs example">
                            <Tab label="Status" {...a11yProps(0)} />
                            <Tab label="Sensors" {...a11yProps(1)} />
                            <Tab label="Network" {...a11yProps(2)} />
                            <Tab label="System" {...a11yProps(3)} />
                            <Tab label="Position" {...a11yProps(4)} />
                        </TabList>
                    </Box>
                    <CustomTabPanel value={value} index={0}>
                        <Status />
                    </CustomTabPanel>
                    <CustomTabPanel value={value} index={1}>
                        <Typography variant="h3" gutterBottom>
                            {t("area.sensors")}
                        </Typography>
                    </CustomTabPanel>
                    <CustomTabPanel value={value} index={2}>
                        <Typography variant="h3" gutterBottom>
                            {t("area.network")}
                        </Typography>
                    </CustomTabPanel>
                    <CustomTabPanel value={value} index={3}>
                        <Typography variant="h3" gutterBottom>
                            {t("area.system")}
                        </Typography>
                    </CustomTabPanel>
                    <CustomTabPanel value={value} index={4}>
                        <Typography variant="h3" gutterBottom>
                            {t("area.position")}
                        </Typography>
                    </CustomTabPanel>
                </TabContext>
            </Box>
        </>
    );
}