/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 * @NModuleScope SameAccount
 * 
 * Bank Details API - Fixed for Python Compatibility
 * Converts all null values to empty strings
 */

define(['N/log', 'N/record', 'N/search'], function(log, record, search) {
    
    var BANK_DETAILS_RECORD = 'customrecord_2663_entity_bank_details';
    var SCRIPT_NAME = 'BankDetailsAPI';
    
    /**
     * Helper function to convert null/undefined to empty string
     * This fixes the Python error: "Only unicode objects are escapable. Got None"
     */
    function nullToEmpty(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return value;
    }
    
    /**
     * Enhanced logging functions
     */
    function logInfo(step, message, data) {
        log.audit({
            title: SCRIPT_NAME + ' - ' + step,
            details: JSON.stringify({
                timestamp: new Date().toISOString(),
                message: message,
                data: data
            }, null, 2)
        });
    }
    
    function logField(fieldName, value, action) {
        log.debug({
            title: SCRIPT_NAME + ' - Field Operation',
            details: JSON.stringify({
                field: fieldName,
                action: action,
                value: typeof value === 'string' && (fieldName.includes('acct') || fieldName.includes('iban')) ? maskSensitive(value) : value,
                timestamp: new Date().toISOString()
            }, null, 2)
        });
    }
    
    function logError(step, error, context) {
        log.error({
            title: SCRIPT_NAME + ' - ERROR at ' + step,
            details: JSON.stringify({
                errorMessage: error.message,
                errorStack: error.stack,
                context: context,
                timestamp: new Date().toISOString()
            }, null, 2)
        });
    }
    
    function maskSensitive(value) {
        if (!value) return '***';
        if (value.length <= 6) return '******';
        return value.substring(0, 3) + '****' + value.substring(value.length - 3);
    }
    
    /**
     * POST endpoint - Create bank details with comprehensive logging
     */
    function doPost(requestBody) {
        var startTime = new Date();
        var requestId = 'REQ_' + startTime.getTime() + '_' + Math.random().toString(36).substr(2, 6);
        
        logInfo('INIT', 'API Call Started', {
            requestId: requestId,
            endpoint: 'POST',
            timestamp: startTime.toISOString()
        });
        
        try {
            // ========== STEP 1: Parse Request Body ==========
            logInfo('STEP1', 'Parsing request body', {
                requestId: requestId,
                rawBodyType: typeof requestBody,
                rawBodyLength: typeof requestBody === 'string' ? requestBody.length : 'N/A'
            });
            
            var data = typeof requestBody === 'string' ? JSON.parse(requestBody) : requestBody;
            
            logInfo('STEP1_COMPLETE', 'Request parsed successfully', {
                requestId: requestId,
                receivedFields: Object.keys(data),
                fieldCount: Object.keys(data).length
            });
            
            // ========== STEP 2: Validate Mandatory Fields ==========
            logInfo('STEP2', 'Validating mandatory fields', {
                requestId: requestId,
                fields: ['vendorId', 'bankType', 'fileFormatId']
            });
            
            var validationErrors = [];
            
            // Validate vendorId
            if (!data.vendorId) {
                validationErrors.push('vendorId is missing');
                logInfo('VALIDATION_FAIL', 'Missing field: vendorId', { requestId: requestId });
            } else {
                logInfo('VALIDATION_PASS', 'Field validated: vendorId', {
                    requestId: requestId,
                    value: data.vendorId
                });
            }
            
            // Validate bankType
            if (!data.bankType) {
                validationErrors.push('bankType is missing');
                logInfo('VALIDATION_FAIL', 'Missing field: bankType', { requestId: requestId });
            } else if (data.bankType !== 'Primary' && data.bankType !== 'Secondary') {
                validationErrors.push('bankType must be "Primary" or "Secondary"');
                logInfo('VALIDATION_FAIL', 'Invalid bankType value', {
                    requestId: requestId,
                    received: data.bankType,
                    expected: ['Primary', 'Secondary']
                });
            } else {
                logInfo('VALIDATION_PASS', 'Field validated: bankType', {
                    requestId: requestId,
                    value: data.bankType
                });
            }
            
            // Validate fileFormatId
            if (!data.fileFormatId) {
                validationErrors.push('fileFormatId is missing');
                logInfo('VALIDATION_FAIL', 'Missing field: fileFormatId', { requestId: requestId });
            } else {
                logInfo('VALIDATION_PASS', 'Field validated: fileFormatId', {
                    requestId: requestId,
                    value: data.fileFormatId
                });
            }
            
            if (validationErrors.length > 0) {
                logInfo('VALIDATION_FAILED', 'Validation completed with errors', {
                    requestId: requestId,
                    errors: validationErrors,
                    validationTime: new Date() - startTime + 'ms'
                });
                
                return {
                    success: false,
                    message: 'Validation failed',
                    errors: validationErrors,
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            // Map bank type
            var bankTypeValue = data.bankType === 'Primary' ? '1' : '2';
            logInfo('FIELD_MAPPING', 'Bank type mapped', {
                requestId: requestId,
                input: data.bankType,
                output: bankTypeValue
            });
            
            // ========== STEP 3: Verify Vendor Exists ==========
            logInfo('STEP3', 'Verifying vendor existence', {
                requestId: requestId,
                vendorId: data.vendorId
            });
            
            var vendorName = '';
            var vendorStartTime = new Date();
            
            try {
                var vendorRecord = record.load({
                    type: 'vendor',
                    id: data.vendorId
                });
                
                vendorName = vendorRecord.getValue({ fieldId: 'entityid' }) || 
                            vendorRecord.getValue({ fieldId: 'companyname' }) || 
                            'Vendor ' + data.vendorId;
                
                var vendorEmail = vendorRecord.getValue({ fieldId: 'email' }) || 'Not Set';
                var vendorLoadTime = new Date() - vendorStartTime;
                
                logInfo('STEP3_COMPLETE', 'Vendor verified successfully', {
                    requestId: requestId,
                    vendorId: data.vendorId,
                    vendorName: vendorName,
                    vendorEmail: vendorEmail,
                    loadTimeMs: vendorLoadTime
                });
                
            } catch (e) {
                logError('Vendor Verification', e, {
                    requestId: requestId,
                    vendorId: data.vendorId
                });
                
                return {
                    success: false,
                    message: 'Vendor not found',
                    error: 'Invalid vendorId: ' + data.vendorId,
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            // ========== STEP 4: Check for Duplicates ==========
            logInfo('STEP4', 'Checking for duplicate records', {
                requestId: requestId,
                vendorId: data.vendorId,
                bankType: data.bankType,
                bankTypeValue: bankTypeValue,
                iban:data.iban
            });
            
            var duplicateStartTime = new Date();
            
            var duplicateSearch = search.create({
                type: BANK_DETAILS_RECORD,
                filters: [
                    ['custrecord_2663_parent_vendor', 'anyof', data.vendorId],
                    'AND',
                    ['custrecord_2663_entity_bank_type', 'anyof', bankTypeValue],
                    'AND',
                    ['custrecord_2663_entity_iban', 'is', data.iban]
                ],
                columns: ['internalid']
            });
            
            var duplicateResults = duplicateSearch.run().getRange({ start: 0, end: 1 });
            var duplicateTime = new Date() - duplicateStartTime;
            
            if (duplicateResults && duplicateResults.length > 0) {
                logInfo('DUPLICATE_FOUND', 'Duplicate record detected', {
                    requestId: requestId,
                    vendorId: data.vendorId,
                    bankType: data.bankType,
                    iban:data.iban,
                    existingRecordId: duplicateResults[0].id,
                    searchTimeMs: duplicateTime
                });
                
                return {
                    success: false,
                    message: 'Bank details already exist for this vendor and bank type and iban',
                    existingRecordId: nullToEmpty(duplicateResults[0].id),
                    vendorName: nullToEmpty(vendorName),
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            logInfo('NO_DUPLICATE', 'No duplicates found', {
                requestId: requestId,
                searchTimeMs: duplicateTime
            });
            
            // ========== STEP 5: Create Record ==========
            logInfo('STEP5', 'Creating new bank detail record', {
                requestId: requestId,
                recordType: BANK_DETAILS_RECORD,
                vendorId: data.vendorId,
                vendorName: vendorName
            });
            
            var createStartTime = new Date();
            var bankRecord = record.create({
                type: BANK_DETAILS_RECORD,
                isDynamic: true
            });
            
            logInfo('RECORD_CREATED', 'Record instance created', {
                requestId: requestId,
                creationTimeMs: new Date() - createStartTime
            });
            
            // ========== STEP 6: Set All Fields with Logging ==========
            var fieldsSet = [];
            var fieldsSkipped = [];
            
            // MANDATORY FIELDS
            
try {
    var recordName = vendorName + ' - ' + data.bankType + ' Bank';
    bankRecord.setValue({
        fieldId: 'name',
        value: recordName
    });
    fieldsSet.push({ field: 'name', value: recordName });
    logField('name', recordName, 'SET');
} catch (e) {
    logError('Set Field', e, { field: 'name' });
    fieldsSkipped.push({ field: 'name', error: e.message });
}          
            // Set Parent Vendor
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_parent_vendor',
                    value: data.vendorId
                });
                fieldsSet.push({ field: 'custrecord_2663_parent_vendor', value: data.vendorId });
                logField('custrecord_2663_parent_vendor', data.vendorId, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_parent_vendor', value: data.vendorId });
                fieldsSkipped.push({ field: 'custrecord_2663_parent_vendor', error: e.message });
            }
            
            // Set Bank Type
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_entity_bank_type',
                    value: bankTypeValue
                });
                fieldsSet.push({ field: 'custrecord_2663_entity_bank_type', value: bankTypeValue });
                logField('custrecord_2663_entity_bank_type', bankTypeValue, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_entity_bank_type', value: bankTypeValue });
                fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_type', error: e.message });
            }
            
            // Set File Format
            try {
                bankRecord.setValue({
                    fieldId: 'custrecord_2663_entity_file_format',
                    value: data.fileFormatId
                });
                fieldsSet.push({ field: 'custrecord_2663_entity_file_format', value: data.fileFormatId });
                logField('custrecord_2663_entity_file_format', data.fileFormatId, 'SET');
            } catch (e) {
                logError('Set Field', e, { field: 'custrecord_2663_entity_file_format', value: data.fileFormatId });
                fieldsSkipped.push({ field: 'custrecord_2663_entity_file_format', error: e.message });
            }
            
            // OPTIONAL FIELDS - Account Information
            if (data.accountNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_no',
                        value: data.accountNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_no', value: '***MASKED***' });
                    logField('custrecord_2663_entity_acct_no', data.accountNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_no', error: e.message });
                }
            }
            
            if (data.accountName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_name',
                        value: data.accountName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_name', value: data.accountName });
                    logField('custrecord_2663_entity_acct_name', data.accountName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_name', error: e.message });
                }
            }
            
            // Bank Information
            if (data.bankNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_no',
                        value: data.bankNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_no', value: data.bankNumber });
                    logField('custrecord_2663_entity_bank_no', data.bankNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_no', error: e.message });
                }
            }
            
            if (data.bankName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_name',
                        value: data.bankName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_name', value: data.bankName });
                    logField('custrecord_2663_entity_bank_name', data.bankName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_name', error: e.message });
                }
            }
            
            if (data.branchNumber) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_branch_no',
                        value: data.branchNumber
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_branch_no', value: data.branchNumber });
                    logField('custrecord_2663_entity_branch_no', data.branchNumber, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_branch_no' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_branch_no', error: e.message });
                }
            }
            
            if (data.branchName) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_branch_name',
                        value: data.branchName
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_branch_name', value: data.branchName });
                    logField('custrecord_2663_entity_branch_name', data.branchName, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_branch_name' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_branch_name', error: e.message });
                }
            }
            
            if (data.accountSuffix) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_acct_suffix',
                        value: data.accountSuffix
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_acct_suffix', value: data.accountSuffix });
                    logField('custrecord_2663_entity_acct_suffix', data.accountSuffix, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_acct_suffix' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_acct_suffix', error: e.message });
                }
            }
            
            if (data.accountType) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_acct_type',
                        value: data.accountType
                    });
                    fieldsSet.push({ field: 'custrecord_2663_acct_type', value: data.accountType });
                    logField('custrecord_2663_acct_type', data.accountType, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_acct_type' });
                    fieldsSkipped.push({ field: 'custrecord_2663_acct_type', error: e.message });
                }
            }
            
            // International Banking
            if (data.iban) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_iban',
                        value: data.iban
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_iban', value: '***MASKED***' });
                    logField('custrecord_2663_entity_iban', data.iban, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_iban' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_iban', error: e.message });
                }
            }
            
            if (data.swift) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_swift',
                        value: data.swift
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_swift', value: data.swift });
                    logField('custrecord_2663_entity_swift', data.swift, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_swift' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_swift', error: e.message });
                }
            }
            
            if (data.bic) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bic',
                        value: data.bic
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bic', value: data.bic });
                    logField('custrecord_2663_entity_bic', data.bic, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bic' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bic', error: e.message });
                }
            }
            
            // Address Information
            if (data.address1) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_address1',
                        value: data.address1
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_address1', value: data.address1 });
                    logField('custrecord_2663_entity_address1', data.address1, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_address1' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_address1', error: e.message });
                }
            }
            
            if (data.address2) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_address2',
                        value: data.address2
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_address2', value: data.address2 });
                    logField('custrecord_2663_entity_address2', data.address2, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_address2' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_address2', error: e.message });
                }
            }
            
            if (data.city) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_city',
                        value: data.city
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_city', value: data.city });
                    logField('custrecord_2663_entity_city', data.city, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_city' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_city', error: e.message });
                }
            }
            
            if (data.state) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_state',
                        value: data.state
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_state', value: data.state });
                    logField('custrecord_2663_entity_state', data.state, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_state' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_state', error: e.message });
                }
            }
            
            if (data.zip) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_zip',
                        value: data.zip
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_zip', value: data.zip });
                    logField('custrecord_2663_entity_zip', data.zip, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_zip' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_zip', error: e.message });
                }
            }
            
            if (data.country) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_country',
                        value: data.country
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_country', value: data.country });
                    logField('custrecord_2663_entity_country', data.country, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_country' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_country', error: e.message });
                }
            }
            
            // Additional Fields
            if (data.customerCode) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_customer_code',
                        value: data.customerCode
                    });
                    fieldsSet.push({ field: 'custrecord_2663_customer_code', value: data.customerCode });
                    logField('custrecord_2663_customer_code', data.customerCode, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_customer_code' });
                    fieldsSkipped.push({ field: 'custrecord_2663_customer_code', error: e.message });
                }
            }
            
            if (data.edi !== undefined) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_edi',
                        value: data.edi
                    });
                    fieldsSet.push({ field: 'custrecord_2663_edi', value: data.edi });
                    logField('custrecord_2663_edi', data.edi, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_edi' });
                    fieldsSkipped.push({ field: 'custrecord_2663_edi', error: e.message });
                }
            }
            
            if (data.babyBonus !== undefined) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_baby_bonus',
                        value: data.babyBonus
                    });
                    fieldsSet.push({ field: 'custrecord_2663_baby_bonus', value: data.babyBonus });
                    logField('custrecord_2663_baby_bonus', data.babyBonus, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_baby_bonus' });
                    fieldsSkipped.push({ field: 'custrecord_2663_baby_bonus', error: e.message });
                }
            }
            
            if (data.chargeBearer) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_chargebearer',
                        value: data.chargeBearer
                    });
                    fieldsSet.push({ field: 'custrecord_chargebearer', value: data.chargeBearer });
                    logField('custrecord_chargebearer', data.chargeBearer, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_chargebearer' });
                    fieldsSkipped.push({ field: 'custrecord_chargebearer', error: e.message });
                }
            }
            
            if (data.bankFeeCode) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_2663_entity_bank_fee_code',
                        value: data.bankFeeCode
                    });
                    fieldsSet.push({ field: 'custrecord_2663_entity_bank_fee_code', value: data.bankFeeCode });
                    logField('custrecord_2663_entity_bank_fee_code', data.bankFeeCode, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_2663_entity_bank_fee_code' });
                    fieldsSkipped.push({ field: 'custrecord_2663_entity_bank_fee_code', error: e.message });
                }
            }
            
            if (data.subsidiaryId) {
                try {
                    bankRecord.setValue({
                        fieldId: 'custrecord_9572_subsidiary',
                        value: data.subsidiaryId
                    });
                    fieldsSet.push({ field: 'custrecord_9572_subsidiary', value: data.subsidiaryId });
                    logField('custrecord_9572_subsidiary', data.subsidiaryId, 'SET');
                } catch (e) {
                    logError('Set Field', e, { field: 'custrecord_9572_subsidiary' });
                    fieldsSkipped.push({ field: 'custrecord_9572_subsidiary', error: e.message });
                }
            }
            
            // Log all fields set
            logInfo('FIELDS_SET', 'All fields processed', {
                requestId: requestId,
                totalFieldsSet: fieldsSet.length,
                totalFieldsSkipped: fieldsSkipped.length,
                fieldsSet: fieldsSet,
                fieldsSkipped: fieldsSkipped,
                setTimeMs: new Date() - createStartTime
            });
            
            // ========== STEP 7: Save Record ==========
            logInfo('STEP7', 'Saving record to NetSuite', {
                requestId: requestId,
                recordId: 'pending',
                fieldsCount: fieldsSet.length
            });
            
            var saveStartTime = new Date();
            var recordId = bankRecord.save();
            var saveTime = new Date() - saveStartTime;
            
            logInfo('RECORD_SAVED', 'Record saved successfully', {
                requestId: requestId,
                recordId: recordId,
                saveTimeMs: saveTime,
                totalProcessingTimeMs: new Date() - startTime
            });
            
            // ========== STEP 8: Return Success Response with null safety ==========
            var totalTime = new Date() - startTime;
            
            var successResponse = {
                success: true,
                message: 'Bank details created successfully',
                data: {
                    recordId: nullToEmpty(recordId),
                    vendorId: nullToEmpty(data.vendorId),
                    vendorName: nullToEmpty(vendorName),
                    bankType: nullToEmpty(data.bankType),
                    fileFormatId: nullToEmpty(data.fileFormatId),
                    fieldsSet: fieldsSet.length,
                    netsuiteUrl: nullToEmpty('https://4533524-sb1.app.netsuite.com/app/common/custom/custrecord.nl?rectype=2663&id=' + recordId)
                },
                metadata: {
                    requestId: nullToEmpty(requestId),
                    processingTimeMs: totalTime,
                    timestamp: new Date().toISOString(),
                    fieldsProcessed: {
                        total: fieldsSet.length,
                        list: fieldsSet.map(function(f) { return nullToEmpty(f.field); })
                    }
                }
            };
            
            logInfo('API_COMPLETE', 'API call completed successfully', {
                requestId: requestId,
                response: successResponse,
                totalTimeMs: totalTime
            });
            
            return successResponse;
            
        } catch (error) {
            var totalTime = new Date() - startTime;
            
            logError('Main Execution', error, {
                requestId: requestId,
                requestBody: typeof requestBody === 'string' ? requestBody.substring(0, 500) : 'Object',
                totalTimeMs: totalTime
            });
            
            return {
                success: false,
                message: 'Failed to create bank details',
                error: nullToEmpty(error.message),
                errorType: nullToEmpty(error.name),
                requestId: nullToEmpty(requestId),
                timestamp: new Date().toISOString(),
                processingTimeMs: totalTime
            };
        }
    }
    
    /**
     * GET endpoint - Retrieve bank details with null safety for Python
     */
    function doGet(requestParams) {
        var startTime = new Date();
        var requestId = 'REQ_' + startTime.getTime() + '_' + Math.random().toString(36).substr(2, 6);
        
        logInfo('GET_INIT', 'GET API Call Started', {
            requestId: requestId,
            params: requestParams,
            timestamp: startTime.toISOString()
        });
        
        try {
            var vendorId = requestParams.vendorId;
            var bankType = requestParams.bankType || 'Primary';
            
            if (!vendorId) {
                logInfo('GET_VALIDATION_FAIL', 'Missing vendorId', {
                    requestId: requestId,
                    receivedParams: requestParams
                });
                
                return {
                    success: false,
                    message: 'vendorId is required',
                    requestId: nullToEmpty(requestId),
                    timestamp: new Date().toISOString()
                };
            }
            
            var bankTypeValue = bankType === 'Primary' ? '1' : '2';
            
            logInfo('GET_SEARCH_START', 'Searching for bank details', {
                requestId: requestId,
                vendorId: vendorId,
                bankType: bankType,
                bankTypeValue: bankTypeValue
                
            });
            
            var searchStartTime = new Date();
            
            var bankSearch = search.create({
                type: BANK_DETAILS_RECORD,
                filters: [
                    ['custrecord_2663_parent_vendor', 'anyof', vendorId],
                    'AND',
                    ['custrecord_2663_entity_bank_type', 'anyof', bankTypeValue]
                ],
                columns: [
                    'internalid',
                    'custrecord_2663_entity_bank_type',
                    'custrecord_2663_entity_file_format',
                    'custrecord_2663_entity_acct_no',
                    'custrecord_2663_entity_acct_name',
                    'custrecord_2663_entity_bank_name',
                    'custrecord_2663_entity_iban',
                    'custrecord_2663_entity_swift'
                ]
            });
            
            var results = [];
            var resultCount = 0;
            
            bankSearch.run().each(function(result) {
                var record = {
                    recordId: nullToEmpty(result.id),
                    bankType: result.getValue('custrecord_2663_entity_bank_type') === '1' ? 'Primary' : 'Secondary',
                    fileFormatId: nullToEmpty(result.getValue('custrecord_2663_entity_file_format')),
                    accountNumber: nullToEmpty(result.getValue('custrecord_2663_entity_acct_no')),
                    accountName: nullToEmpty(result.getValue('custrecord_2663_entity_acct_name')),
                    bankName: nullToEmpty(result.getValue('custrecord_2663_entity_bank_name')),
                    iban: nullToEmpty(result.getValue('custrecord_2663_entity_iban')),
                    swift: nullToEmpty(result.getValue('custrecord_2663_entity_swift'))
                };
                results.push(record);
                resultCount++;
                return true;
            });
            
            var searchTime = new Date() - searchStartTime;
            var totalTime = new Date() - startTime;
            
            logInfo('GET_SEARCH_COMPLETE', 'Search completed', {
                requestId: requestId,
                vendorId: vendorId,
                bankType: bankType,
                recordsFound: resultCount,
                searchTimeMs: searchTime,
                totalTimeMs: totalTime
            });
            
            return {
                success: true,
                data: {
                    vendorId: nullToEmpty(vendorId),
                    bankType: nullToEmpty(bankType),
                    records: results,
                    count: results.length
                },
                metadata: {
                    requestId: nullToEmpty(requestId),
                    processingTimeMs: totalTime,
                    timestamp: new Date().toISOString()
                }
            };
            
        } catch (error) {
            var totalTime = new Date() - startTime;
            
            logError('GET Execution', error, {
                requestId: requestId,
                params: requestParams,
                totalTimeMs: totalTime
            });
            
            return {
                success: false,
                message: nullToEmpty(error.message),
                requestId: nullToEmpty(requestId),
                timestamp: new Date().toISOString(),
                processingTimeMs: totalTime
            };
        }
    }
    
    return {
        post: doPost,
        get: doGet
    };
});